import Sofa
import numpy as np
import pandas as pd


class Controller(Sofa.Core.Controller):
    def __init__(self, *args, **kwargs):
        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.pressure_cavity_1 = kwargs['pressure_cavity_1']
        self.pressure_cavity_2 = kwargs['pressure_cavity_2']
        self.pressure_cavity_3 = kwargs['pressure_cavity_3']
        self.tip_roi = kwargs['tip_roi']
        self.index = 0
        self.input_pressures_1 = kwargs['input_pressures_1']
        self.input_pressures_2 = kwargs['input_pressures_2']
        self.input_pressures_3 = kwargs['input_pressures_3']
        self.csv_file = "data.csv"
        with open(self.csv_file, "w", newline="") as f:
            df_header = pd.DataFrame({"1": ["pressure1"], "2": ["pressure2"], "3": ["pressure3"],
                                      "4": ["tipX"], "5": ["tipY"], "6": ["tipZ"]})
            df_header.to_csv(f, header=False, index=False)
            f.close()

    def update_pressure(self, pressure_cavity, input_pressures):
        if self.index < len(input_pressures):
            pressure_cavity.pressure.value = input_pressures[self.index]

    def onAnimateEndEvent(self, _: dict):
        self.update_pressure(self.pressure_cavity_1, self.input_pressures_1)
        self.update_pressure(self.pressure_cavity_2, self.input_pressures_2)
        self.update_pressure(self.pressure_cavity_3, self.input_pressures_3)
        self.index += 1

        tip_position_mm = 1000*np.mean(self.tip_roi.position.value, axis=0)
        print(tip_position_mm)
        df = pd.DataFrame({
            "pressure_1": [self.pressure_cavity_1.pressure.value],
            "pressure_2": [self.pressure_cavity_2.pressure.value],
            "pressure_3": [self.pressure_cavity_3.pressure.value],
            "tipX": tip_position_mm[0],
            "tipY": tip_position_mm[1],
            "tipZ": tip_position_mm[2],
        })
        with open(self.csv_file, "a", newline="") as f:
            df.to_csv(f, header=False, index=False)
            f.close()
