import Sofa
import numpy as np
import pandas as pd


class Controller(Sofa.Core.Controller):
    def __init__(self, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.pressure_1 = kwargs['pressure_cavity_1']
        self.pressure_2 = kwargs['pressure_cavity_2']
        self.pressure_3 = kwargs['pressure_cavity_3']
        self.tip_roi = kwargs['tip_roi']
        self.index = 0
        self.input_pressures_1 = np.linspace(0, 10000, 500)
        self.csv_file = "data.csv"
        with open(self.csv_file, "w", newline="") as f:
            df_header = pd.DataFrame({"1": ["pressure1"], "2": ["pressure2"], "3": ["pressure3"],
                                      "4": ["tipX"], "5": ["tipY"], "6": ["tipZ"]})
            df_header.to_csv(f, header=False, index=False)
            f.close()

    def onAnimateEndEvent(self, e: dict):
        if self.index < len(self.input_pressures_1):
            pressure_1 = self.input_pressures_1[self.index]
            self.pressure_1.pressure.value = pressure_1
            self.index += 1
            print("New Pressure {}".format(self.pressure_1.pressure.value))
            tip_position_mm = 1000*np.mean(self.tip_roi.position.value, axis=0)
            print(tip_position_mm)
            df = pd.DataFrame({
                "pressure_1": [pressure_1],
                "pressure_2": [0],
                "pressure_3": [0],
                "tipX": tip_position_mm[0],
                "tipY": tip_position_mm[1],
                "tipZ": tip_position_mm[2],
            })
            with open(self.csv_file, "a", newline="") as f:
                df.to_csv(f, header=False, index=False)
                f.close()
