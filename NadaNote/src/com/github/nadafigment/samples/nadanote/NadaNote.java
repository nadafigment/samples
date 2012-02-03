 
package com.github.nadafigment.samples.nadanote;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnKeyListener;
import android.widget.AdapterView.AdapterContextMenuInfo;
import android.widget.EditText;
import android.widget.SimpleCursorAdapter;

public class NadaNote extends Activity {
    private static final int CREATE_ID = Menu.FIRST;
    private static final int OPEN_ID = Menu.FIRST + 1;
    private static final int DELETE_ID = Menu.FIRST + 2;
    

    private EditText mBodyText;
    private Long mRowId;
    private NotesDbAdapter mDbHelper;

    /** Called when the activity is first created. */
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        mDbHelper = new NotesDbAdapter(this);
        mDbHelper.open();
        
        setContentView(R.layout.note_edit);
        setTitle(R.string.edit_note);

        mBodyText = (EditText) findViewById(R.id.body);

        mRowId = (savedInstanceState == null) ? null :
            (Long) savedInstanceState.getSerializable(NotesDbAdapter.KEY_ROWID);
        if (mRowId == null) {
            Bundle extras = getIntent().getExtras();
            mRowId = extras != null ? extras.getLong(NotesDbAdapter.KEY_ROWID)
                                    : null;
        }
        
        populateFields();
        
        updateFromData();
        
        //registerForContextMenu(getListView());
        
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
            Cursor note = mDbHelper.fetchNote(mRowId);
            startManagingCursor(note);
            mBodyText.setText(note.getString(
                    note.getColumnIndexOrThrow(NotesDbAdapter.KEY_BODY)));
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

    private void fillData() {
        // Get all of the rows from the database and create the item list
        Cursor notesCursor = mDbHelper.fetchAllNotes();
        startManagingCursor(notesCursor);

        // Create an array to specify the fields we want to display in the list (only TITLE)
        String[] from = new String[]{NotesDbAdapter.KEY_TITLE};

        // and an array of the fields we want to bind those fields to (in this case just text1)
        int[] to = new int[]{R.id.text1};

        // Now create a simple cursor adapter and set it to display
        SimpleCursorAdapter notes = 
            new SimpleCursorAdapter(this, R.layout.notes_row, notesCursor, from, to);
        //setListAdapter(notes);
    }
    
    public void onDataChanged() {
    	// eventually we'd start a timer so we don't do this all at once. But for now, just call
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
            	return true;
            case DELETE_ID:
                AdapterContextMenuInfo info = (AdapterContextMenuInfo) item.getMenuInfo();
                mDbHelper.deleteNote(info.id);
                fillData();
                return true;
        }

        return super.onMenuItemSelected(featureId, item);
    }

    private void createNote() {
    	mRowId = null;
    	populateFields();
    	updateFromData();
    }
    
    private void openNote(long id) {
    	mRowId = id;
    	populateFields();
    	updateFromData();
    }

    /*
    @Override
    protected void onListItemClick(ListView l, View v, int position, long id) {
        super.onListItemClick(l, v, position, id);
        openNote(id);
    }
    */
    

    /* (non-Javadoc)
	 * @see android.app.Activity#registerForContextMenu(android.view.View)
	 */
	@Override
	public void registerForContextMenu(View view) {
		super.registerForContextMenu(view);
	}


    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent intent) {
        super.onActivityResult(requestCode, resultCode, intent);
        fillData();
    }
}
