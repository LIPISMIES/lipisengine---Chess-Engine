
/*
Mitä asioita shakissa on:
- nappulat
- nappulatyyppi
- väri
- lauta
- ruutu
- siirto
- vuoro
- säännöt
 */


 #[derive(Clone, Copy, PartialEq, Eq)]
pub struct Square {
    pub file: char,
    pub rank: char,
}

pub const FILES: [char; 8] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

pub const RANKS: [char; 8] = ['1', '2', '3', '4', '5', '6', '7', '8'];

pub fn print_all_squares () {
    for rank in RANKS {
        for file in FILES {
            print!("{}{}, ", file, rank);
        }
        println!("");
    }
}

const fn generate_all_squares() -> [Square; 64] {
    let example_sq: Square = Square{file: 'A', rank: '1'};
    let mut all_squares: [Square; 64] = [example_sq; 64];
    let mut i:usize  = 0;
    let mut rank_index = 0;

    while rank_index < 8 {
        let mut file_index = 0;
        while file_index < 8 {
            let file: char = FILES[file_index];
            let rank: char = RANKS[rank_index];
            let sq: Square = Square{file, rank};
            all_squares[i] = sq;
            i += 1;
            file_index += 1;
        }
        rank_index += 1;
    }
    all_squares
}

pub const ALL_SQUARES: [Square; 64] = generate_all_squares();
