use std::process::Command;

use pty::fork::{
    Fork,
    Master,
};

pub fn child_command(command: String, argv: Vec<String>) {
    /// command: name of shell command to run
    /// argv: vec of args, not including command
    /// like execvp
    /// this should be called from a child process
    
    Command::new(command)
        .args(argv)
        //.env(...)
        .spawn()
        .expect("Couldn't execute " + command);
}

pub fn pty_fork() -> Fork {
    Fork::from_ptmx().unwrap() // TODO: handle error
}

pub fn pty_master(fork: Fork) -> Option<Master> {
    /// returns Some(master) if we're parent
    /// or None if we're child
    fork.is_parent().ok()
}
