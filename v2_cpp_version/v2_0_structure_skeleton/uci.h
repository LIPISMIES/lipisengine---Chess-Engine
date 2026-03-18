// uci.h
/*
 * UCI class definition
 * Responsible for handling the Universal Chess Interface (UCI) communication loop.
 * Provides the interface for parsing commands and responding accordingly.
 */

#pragma once

class UCI {
public:
    // Main loop for processing UCI commands from standard input
    void loop();
};
