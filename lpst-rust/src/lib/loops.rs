use std::fs;
use std::io;
use futures::select;

pub fn record_loop(master: fs::File, transcript: &mut Transcript) {
    let stdout = LpstReader::new(master);
    let stdin = LpstReader::new(io::stdin());

    loop {
        select! {
            data = stdin.read() => {
                master.write_all(data); // TODO translate to strnig or whatever
                transcript.input(data);
                stdout.add_echo(data);
                stdout.set_time();
            },
            data = stdout.read() => {
                if data.empty()
                    break;
                data = stdout.remove_echo(data);
                if stdout.check_overtime()
                    transcript.wait(stdout.wait);
                transcript.output(data);
                print!("{}", String::from_utf8(data));
            },
        }
    }
    // TODO: oserror?
}
