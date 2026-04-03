import os, pty, sys, shutil
from transcript import Transcript
from station import child_execvp, parent_loop

def record(program: str, args: list[str]):
    if not shutil.which(program):
        sys.exit(f"Loopstation: File {program} not found, check $PATH?")
    else:
        print("--- LOOPSTATION: STARTING RECORDING ---")

    # Start transcript with our argv
    header = f"$ [{program}]"
    for arg in args:
        header += f" [{arg}]"
    transcript = Transcript(header)

    # Fork!
    pid, master_fd = pty.fork()

    # we're child, become program
    if pid == 0:
        return child_execvp([program] + args)

    # otherwise, we're parent
    # TODO: make this robust against args with [] in them
    try:
        parent_loop(master_fd, transcript)
    except OSError as e:
        if e.errno == 5: # IO error
            print("--- LOOPSTATION: PROGRAM EXITED ---\n")
        else: raise e
    print("Loopstation: Recorded!")
    finish_recording(program, transcript)

def finish_recording(program: str, transcript: Transcript):
    while True:
        match input("Loopstation: [s]ave/[v]iew recording/[q]uit - "):
            case 'v':
                transcript.print()
            case 'q':
                print("\nLoopstation: Exiting without saving transcript")
                return
            case 's':
                # TODO: how to conveniently ask user for default dir
                # lpst record [-d {dir}] {program}?
                default_dir = os.path.join(os.getcwd(), program + '-lpst')
                os.makedirs(default_dir, exist_ok=True)
                print(f"Loopstation: Saving in directory {default_dir}.")
                # TODO: windows vs unix
                while not (name := input("Loopstation: Enter test name - ")):
                    pass
                try:
                    filename = name + '.lpst'
                    with open(os.path.join(default_dir, filename), 'x') as f:
                        transcript.save(f)
                        print(f"Loopstation: Saved to {filename}")
                    return
                except FileExistsError:
                    print(f"Loopstation: {filename} already exists!")
                # TODO: handle other errors
            case _:
                pass
