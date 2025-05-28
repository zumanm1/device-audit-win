import sys

OUTPUT_FILE = "/root/za-con/test_print_output.txt"

message = "--- MINIMAL PYTHON TEST: Output from test_print.py written to file ---"

try:
    with open(OUTPUT_FILE, 'w') as f:
        f.write(message + "\n")
        f.write("--- MINIMAL PYTHON TEST: File write successful ---\n")
    # To indicate success to the outside world, if we can't see prints
    # we could try creating a success marker file, but let's see if this works first
except Exception as e:
    # If file writing fails, try to write that error to another file
    # This is getting meta, but we need some signal
    try:
        with open("/root/za-con/test_print_error.txt", 'w') as f_err:
            f_err.write(f"Failed to write to {OUTPUT_FILE}: {str(e)}\n")
    except:
        pass # At this point, we're out of easy options to signal failure
