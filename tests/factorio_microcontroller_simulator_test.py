from pathlib import Path
import unittest

from simulator.factorio_microcontroller_sim import FactorioMicrocontrollerSim

TEST_RESOURCE_FOLDER = Path(__file__).parent.parent / "tests/resources"


class FactorioMicrocontrollerSimTest(unittest.TestCase):
    def setUp(self):
        fib_binary_file = TEST_RESOURCE_FOLDER / "fibonacci_binary.txt"
        self.simulator = FactorioMicrocontrollerSim(fib_binary_file)

    def test_simulate_fibonacci(self):
        state = self.simulator.simulate(verbose=False, enable_igpu_sim=False)

        self.assertEqual(0, state.output_registers[0])
        self.assertEqual(5, state.output_registers[1])


if __name__ == '__main__':
    unittest.main()
