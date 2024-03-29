[![Checks](https://github.com/Maurits825/factorio-microcontroller/actions/workflows/factorio-microcontroller.yml/badge.svg)](https://github.com/Maurits825/factorio-microcontroller/actions)

# Factorio-Microcontroller
This project contains scripts and docs for a microcontroller made in the game [Factorio](https://www.factorio.com/).

## Overview
![factorio microcontroller](img/factorio-cpu-v2.png)
Screenshot of the microcontroller showing each part.

## Getting Started

### Compile a Program
The assembly programs have to be written using this [Assembly language](https://github.com/Maurits825/factorio-microcontroller/wiki/Assembly-Language).

Run the `setup.sh` script only once to create the virtual environment and download the dependencies.

To compile the program, double click the `start_microcontroller.sh` script.  
Use `python factorio_microcontroller.py -a (file_name)` to compile your program, with the optional `-c` flag to copy the blueprint to the clipboard.  
For example: `python factorio_microcontroller.py -a ../programs/counter.txt -c`  
This also creates a binary file name _file_name_binary_ in the programs folder.

### Run a Program
Import the blueprint into Factorio. Place it on the left side of the ROM. Connect it to the constant combinator with the signal `i` as shown below.  
![program memory](img/program-memory.png)

Turn the reset combinator on and off to reset the microcontroller. Enable the clock to start the program.

In sandbox mode the game speed can be increased to increase the speed of the clock. At default speed, the clock runs at 0.75 Hz, each instruction takes two cyles to complete.

## Microcontroller Simulator
The simulator simulates the microcontroller and can be useful to debug assembly programs. Run the `start_simulator.sh` script to use it.
