"""터미널/크론용: python run_daily.py [--demo]"""
import sys

import pipeline

if __name__ == "__main__":
    for m in pipeline.run_all(demo="--demo" in sys.argv):
        print(m)
    print("완료:", pipeline.today())
