def main():
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Main Function Except")
        raise Exception("MainFunctionException")
        


if __name__ == "__main__":
    try:
        print("Main Function Start")
        main()
    except Exception as e:
        print("Root Except: ", e)
            