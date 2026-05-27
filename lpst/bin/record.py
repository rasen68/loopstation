import os, pty, sys, shutil
from lpst.lib.transcript import Transcript
from lpst.lib.station import child_execvp, record_loop

def record(argv: list[str]):
    if not shutil.which(argv[0]):
        sys.exit(f"Loopstation: File {argv[0]} not found, check $PATH?")
    else:
        print("--- LOOPSTATION: STARTING RECORDING ---")

    # Start transcript with our argv
    transcript = Transcript(argv)

    # Fork!
    pid, master_fd = pty.fork()

    # we're child, become program
    if pid == 0:
        return child_execvp(argv)

    # otherwise, we're parent
    record_loop(master_fd, transcript)
    print("--- LOOPSTATION: RECORDING FINISHED ---")
    finish_recording(argv[0], transcript)

def finish_recording(program: str, transcript: Transcript):
    while True:
        match input("Loopstation: [s]ave/[v]iew recording/[q]uit - "):
            case 'v':
                transcript.print()
            case 'q':
                print("\nExiting without saving transcript")
                return
            case 's':
                # TODO: how to conveniently ask user for default dir
                # lpst record [-d {dir}] {program}?
                default_dir = os.path.join(os.getcwd(), program + '-lpst')
                os.makedirs(default_dir, exist_ok=True)
                print(f"Saving in directory {default_dir}.")
                while not (name := input("Enter test name - ")):
                    pass
                try:
                    filename = "lpst." + name + '.json'
                    fullname = os.path.join(default_dir, filename)
                    transcript.save(fullname)
                    print(f"Saved to {filename}")
                    return
                except FileExistsError:
                    print(f"{filename} already exists! Replace? [y/N] ", end='')
                    if input().upper() == 'Y':
                        os.remove(fullname)
                        transcript.save(fullname)
                        print(f"Saved to {filename}")
                        return
            case _:
                pass
