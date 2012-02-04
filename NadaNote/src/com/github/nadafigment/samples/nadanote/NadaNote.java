 
package com.github.nadafigment.samples.nadanote;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.SQLException;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnKeyListener;
import android.widget.EditText;

public class NadaNote extends Activity {
	private static final int ACTIVITY_OPEN=1;

	private static final int CREATE_ID = Menu.FIRST;
    private static final int OPEN_ID = Menu.FIRST + 1;    
    
    public static final String KEY_LAST_NOTE = "last_note";

    // we shouldn't really do this, but this is just for debugging, logging etc
    public static final String APP_TAG = "NadaNote";
    
    private EditText mBodyText;
    private Long mRowId;
    private NotesDbAdapter mDbHelper;
    private SharedPreferences mPrefs;

    /** Called when the activity is first created. */
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        mDbHelper = new NotesDbAdapter(this);
        mDbHelper.open();
        
        setContentView(R.layout.note_edit);
        setTitle(R.string.edit_note);
        
        mPrefs = getSharedPreferences(getString(R.string.app_name), Context.MODE_PRIVATE);

        mBodyText = (EditText) findViewById(R.id.body);

        mRowId = null;
        Bundle extras = getIntent().getExtras();
        if (extras != null) {
        	long rowid = extras.getLong(NotesDbAdapter.KEY_ROWID);
        	mRowId = rowid == -1 ? null : rowid;
        	Log.i(APP_TAG, "got bundle in create " + rowid);
        }
        else {
        	if (savedInstanceState == null) {
        		long lastRow = mPrefs.getLong(KEY_LAST_NOTE, -1);
        		mRowId = lastRow == -1 ? null : lastRow;
        	}
        	else {
        		mRowId = (Long) savedInstanceState.getSerializable(NotesDbAdapter.KEY_ROWID);
        	}
        }        
        Log.i(APP_TAG, "OnCreate called, with mRowId: " + mRowId);
        
        populateFields();
        
        updateFromData();
        
        mBodyText.setOnKeyListener(new OnKeyListener() {
            public boolean onKey(View v, int keyCode, KeyEvent event) {
                // If the event is a key-down event on the "enter" button
                if ((event.getAction() == KeyEvent.ACTION_UP) &&
                		((event.getKeyCode() != KeyEvent.KEYCODE_MENU) &&
                				(event.getKeyCode() != KeyEvent.KEYCODE_HOME) &&
                				(event.getKeyCode() != KeyEvent.KEYCODE_BACK) &&
                				(event.getKeyCode() != KeyEvent.KEYCODE_SEARCH))) {
                	// Perform action on key press
                	NadaNote.this.onDataChanged();
                	return true;
                }
                return false;
            }
        });

    }
    
	private void populateFields() {
        if (mRowId != null) {
        	try {
        		Cursor note = mDbHelper.fetchNote(mRowId);
        		startManagingCursor(note);
        		mBodyText.setText(note.getString(
        				note.getColumnIndexOrThrow(NotesDbAdapter.KEY_BODY)));
        		Log.i(APP_TAG, "Opened note " + mRowId);
        	}
        	catch (Exception e) {
        		
        		Log.e(APP_TAG, "Could not find note " + mRowId);
        		Log.wtf(APP_TAG, Log.getStackTraceString(e));
        		
        		mRowId = null;
        		mBodyText.setText("");
        	}
        }
        else {
        	mBodyText.setText("");
        }
    }
    
    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        saveState();
        outState.putSerializable(NotesDbAdapter.KEY_ROWID, mRowId);
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        
        saveState();
        
        SharedPreferences.Editor ed = mPrefs.edit();
        ed.putLong(KEY_LAST_NOTE, mRowId);
        ed.commit();
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        populateFields();
    }
    
    private void saveState() {
        String body = mBodyText.getText().toString();
        String title = getNoteTitle();

        if (mRowId == null) {
            long id = mDbHelper.createNote(title, body);
            if (id > 0) {
                mRowId = id;
            }
        } else {
            mDbHelper.updateNote(mRowId, title, body);
        }
    }
    
    private String getNoteTitle() {
    	
    	String title;
    	String body = mBodyText.getText().toString();
    	String line;
    	int firstCR = body.indexOf('\n');
    	if (-1 == firstCR) {
    		line = body;
    	}
    	else {
    		line = body.substring(0, firstCR);
    	}
    	line = line.trim();
    	if (line.isEmpty()) {
    		title = "Untitled";	
    	}
    	else {
    		title = line;
    	}
    	return title;
    }

    public void onDataChanged() {
    	// eventually we'd start a timer so we don't do this 
    	// all at once. But for now, just call
    	dataChanged();
    }
    
    private void dataChanged() {
    	saveState();
    	updateFromData();
    }
    
    private void updateFromData() {
    	String title = getString(R.string.edit_note) + " - " + getNoteTitle();
    	setTitle(title);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
    	saveState();
        super.onCreateOptionsMenu(menu);
        menu.add(0, CREATE_ID, 0, R.string.menu_create);
        menu.add(0, OPEN_ID, 0, R.string.menu_open);
        // only if we have a saved one??
        //menu.add(0, DELETE_ID, 0, R.string.menu_delete);
        return true;
    }

    @Override
    public boolean onMenuItemSelected(int featureId, MenuItem item) {
        switch(item.getItemId()) {
            case CREATE_ID:
                createNote();
                return true;
            case OPEN_ID:
            	openNote();
            	return true;
        }

        return super.onMenuItemSelected(featureId, item);
    }

    private void createNote() {
    	mRowId = null;
    	populateFields();
    	updateFromData();
    }
    
    private void openNote() {
    	Intent i = new Intent(this, NotePicker.class);
        startActivityForResult(i, ACTIVITY_OPEN);
    }

	@Override
	public void registerForContextMenu(View view) {
		super.registerForContextMenu(view);
	}
	
	@Override
	protected void onActivityResult(int requestCode, int resultCode, Intent data) {
		super.onActivityResult(requestCode, resultCode, data);
		
		if (ACTIVITY_OPEN == requestCode) {
			if (RESULT_OK == resultCode) {
				Bundle extras = data.getExtras();
				mRowId = extras != null ? extras.getLong(NotesDbAdapter.KEY_ROWID)
										: null;
       
				populateFields();
				updateFromData();
			}
		}
	}

}
