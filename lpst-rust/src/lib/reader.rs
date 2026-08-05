use std::fs;
use std::time;;

struct LpstReader {
    file: &mut impl Read,
    echo: mut Vec<u8>,
    time: time::Instant,
    wait: time::Duration,
    min_wait: time::Duration,
    //deferred: Vec<u8>,
}

impl LpstReader {
    pub fn new(file: &mut impl Read) -> Self {
        Self {
            file: file,
            echo: Vec::new(),
            time: time::Instant::now(),
            wait: time::Duration::from_secs(0),
            min_wait: time::Duration::from_secs(1), // TODO: this should be an option
        }
    }

    pub fn read(&mut self) -> Vec<u8> {
        // TODO: correct way to do this
        // TODO: chunk / deferred?
        let mut buf = Vec::new(); 
        let _size = fs::read_to_end(self.file, &buf)?; // TODO: handle error
        buf
    }

    pub fn add_echo(&mut self, data: Vec<u8>) {
        self.echo.extend(data); // TODO: copy?
    }

    pub fn set_time(&mut self) {
        self.time = time::Instant::now();
    }

    pub fn check_overtime(&mut self) -> bool {
        let self.wait = time::Instant::now() - self.time;
        self.set_time();
        self.wait > min_wait
    }

    pub fn remove_echo(&mut self, data: Vec<u8>) -> Vec<u8> {
        let echo_len = self.echo.len();
        let data_len = self.data.len();
        if echo_len < data_len && self.echo[..data_len] == data {
            self.echo = self.echo[data_len..];
            return Vec::new();
        } else data[..echo_len] == self.echo {
            self.echo = Vec::new();
            return data[..echo_len];
        }
        return data;
    }
}
