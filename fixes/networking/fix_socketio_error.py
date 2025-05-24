#!/usr/bin/env python3

import os
import re

def fix_socketio_patching(input_filepath, output_filepath):
    """
    Fixes the Socket.IO patching code by adding a check for io and io.Socket
    before attempting to patch the prototype.
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # The problematic Socket.IO patching code
    socketio_patch_pattern = r"""    // Patch Socket.IO event handlers to catch errors
    const originalOn = io.Socket.prototype.on;
    io.Socket.prototype.on = function\(event, callback\) \{
        const wrappedCallback = function\(\.\.\.[^}]+\}\);
    \};"""

    # The fixed Socket.IO patching code with a check for io and io.Socket
    fixed_socketio_patch = """    // Patch Socket.IO event handlers to catch errors
    if (typeof io !== 'undefined' && io && io.Socket && io.Socket.prototype) {
        const originalOn = io.Socket.prototype.on;
        io.Socket.prototype.on = function(event, callback) {
            const wrappedCallback = function(...args) {
                try {
                    return callback.apply(this, args);
                } catch (error) {
                    window.errorBoundary.handleComponentError(
                        'socket-' + event, 
                        'Socket.IO Event: ' + event, 
                        error, 
                        { eventArgs: args }
                    );
                }
            };
            return originalOn.call(this, event, wrappedCallback);
        };
    } else {
        console.warn('Socket.IO not available yet, skipping event handler patching');
    }"""

    print("Applying Socket.IO patching fix...")
    
    # Use a more flexible approach to find and replace the Socket.IO patching code
    # Look for the start of the patching code
    patch_start = "    // Patch Socket.IO event handlers to catch errors"
    patch_end = "    };"
    
    if patch_start in content:
        # Find the start index of the patching code
        start_index = content.find(patch_start)
        if start_index != -1:
            # Find the end index of the patching code
            end_index = content.find(patch_end, start_index)
            if end_index != -1:
                # Include the end pattern in the replacement
                end_index += len(patch_end)
                # Extract the original code
                original_code = content[start_index:end_index]
                # Replace with the fixed code
                content = content[:start_index] + fixed_socketio_patch + content[end_index:]
                print("Fix applied successfully.")
            else:
                print("Warning: Could not find the end of the Socket.IO patching code.")
                return False
        else:
            print("Warning: Could not find the start of the Socket.IO patching code.")
            return False
    else:
        print("Warning: Socket.IO patching code not found in the file.")
        return False

    print(f"Writing modified content to: {output_filepath}")
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing to file '{output_filepath}': {e}")
        return False
        
    return True

if __name__ == "__main__":
    input_file = "/root/za-con/rr3-router.py"
    output_file = "/root/za-con/rr3-router.py.fixed"
    
    if fix_socketio_patching(input_file, output_file):
        print(f"Socket.IO patching fix applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply Socket.IO patching fix.")
