// This is a comment, and is ignored by the compiler.
// You can test this code by clicking the "Run" button over there ->
// or if you prefer to use your keyboard, you can use the "Ctrl + Enter"
// shortcut.

// This code is editable, feel free to hack it!
// You can always return to the original code by clicking the "Reset" button ->

// This is the main function.

use crate::types::{RANKS, FILES, Square, print_all_squares};

mod types;
mod movegen;



fn main() {
    let square1: Square = Square{file: FILES[0], rank: RANKS[0]};   
    print_all_squares();
    println!("{}{}", square1.file, square1.rank);
}