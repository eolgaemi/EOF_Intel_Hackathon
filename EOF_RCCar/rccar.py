import time
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from gpiozero import PWMOutputDevice, DigitalOutputDevice, DigitalInputDevice, Motor
from statistics import median

# GPIO 핀 설정
TRIGGER_PIN_1 = 17
ECHO_PIN_1 = 18
TRIGGER_PIN_2 = 22
ECHO_PIN_2 = 23
TRIGGER_PIN_3 = 9
ECHO_PIN_3 = 25
PWMA = 12
AIN1 = 16
AIN2 = 20
PWMB = 13
BIN1 = 19
BIN2 = 26

# 트리거 및 에코 장치 설정
trigger_1 = DigitalOutputDevice(TRIGGER_PIN_1)
echo_1 = DigitalInputDevice(ECHO_PIN_1)
trigger_2 = DigitalOutputDevice(TRIGGER_PIN_2)
echo_2 = DigitalInputDevice(ECHO_PIN_2)
trigger_3 = DigitalOutputDevice(TRIGGER_PIN_3)
echo_3 = DigitalInputDevice(ECHO_PIN_3)

# 모터 객체 생성 및 PWMOutputDevice 초기화
L_Motor = PWMOutputDevice(PWMA)
R_Motor = PWMOutputDevice(PWMB)

# 방향 제어 핀 설정
AIN1_pin = DigitalOutputDevice(AIN1)
AIN2_pin = DigitalOutputDevice(AIN2)
BIN1_pin = DigitalOutputDevice(BIN1)
BIN2_pin = DigitalOutputDevice(BIN2)

def get_distance(trigger, echo):
    trigger.off()
    time.sleep(0.1)
    trigger.on()
    time.sleep(0.00001)
    trigger.off()
    start_time = time.time()
    while echo.is_active == False:
        start_time = time.time()
    while echo.is_active == True:
        end_time = time.time()
    time_elapsed = end_time - start_time
    distance = (time_elapsed * 34300) / 2
    if distance >= 23 :
        distance = 23
    return distance

def get_median_distance(trigger, echo, samples=5):
    distances = []
    for _ in range(samples):
        distance = get_distance(trigger, echo)
        if distance > 0:
            distances.append(distance)
        time.sleep(0.05)
    if distances:
        return median(distances)
    else:
        return float('inf')

def motor_back(speed):
    L_Motor.value = speed
    AIN2_pin.off()
    AIN1_pin.on()
    R_Motor.value = speed
    BIN2_pin.off()
    BIN1_pin.on()

def motor_go(speed):
    L_Motor.value = speed
    AIN2_pin.on()
    AIN1_pin.off()
    R_Motor.value = speed
    BIN2_pin.on()
    BIN1_pin.off()

def motor_stop():
    L_Motor.value = 0
    R_Motor.value = 0

def motor_right(speed):
    L_Motor.value = speed
    AIN2_pin.on()
    AIN1_pin.off()
    R_Motor.value = speed
    BIN2_pin.off()
    BIN1_pin.on()

def motor_left(speed):
    L_Motor.value = speed
    AIN2_pin.off()
    AIN1_pin.on()
    R_Motor.value = speed
    BIN2_pin.on()
    BIN1_pin.off()

def motor_control(command, speed=0.7):
    if command == "go":
        L_Motor.value = speed
        AIN2_pin.on()
        AIN1_pin.off()
        R_Motor.value = speed
        BIN2_pin.on()
        BIN1_pin.off()
    elif command == "back":
        L_Motor.value = speed
        AIN2_pin.off()
        AIN1_pin.on()
        R_Motor.value = speed
        BIN2_pin.off()
        BIN1_pin.on()
    elif command == "stop":
        L_Motor.value = 0
        R_Motor.value = 0
    elif command == "right":
        L_Motor.value = speed
        AIN2_pin.on()
        AIN1_pin.off()
        R_Motor.value = speed
        BIN2_pin.off()
        BIN1_pin.on()
    elif command == "left":
        L_Motor.value = speed
        AIN2_pin.off()
        AIN1_pin.on()
        R_Motor.value = speed
        BIN2_pin.on()
        BIN1_pin.off()


def img_preprocess(image):
    height, _, _ = image.shape
    image = image[:, :, :]
    #image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    image = cv2.resize(image, (128,96))
    image = cv2.GaussianBlur(image,(5,5),0)
    #_, image = cv2.threshold(image,95,255,cv2.THRESH_BINARY_INV)
    image = image / 255
    return image

camera = cv2.VideoCapture(0)
camera.set(3, 640)
camera.set(4, 480)

def main():
    #model_path = '/home/test/Downloads/model0601.h5'
    model_path = '/home/test/Downloads/model_lane_tracer.h5'
    model = load_model(model_path)
    
    carState = "stop"
    speedSet = 0.6
    use_sensor = True
    count = 0
    try:
        while True:
            if use_sensor:
                distance1 = get_median_distance(trigger_1, echo_1)
                distance2 = get_median_distance(trigger_2, echo_2)
                distance3 = get_median_distance(trigger_3, echo_3)
                print("Distance1 => {:.2f} cm".format(distance1))
                print("Distance2 => {:.2f} cm".format(distance2))
                print("Distance3 => {:.2f} cm".format(distance3))
                if distance1 <= 7 or distance2 <= 7 or distance3 <= 7:
                    count = count + 1
                    time.sleep(0.5)
                else :
                    count = 0

                if carState == "stop" and count == 3:
                    print("Start driving")
                    carState = "go"
                    use_sensor = False

            keyValue = cv2.waitKey(1)
            if keyValue == ord('q'):
                break

            if carState == "go":
                _, image = camera.read()
                preprocessed = img_preprocess(image)
                cv2.imshow('pre', preprocessed)

                X = np.asarray([preprocessed])
                steering_angle = int(model.predict(X)[0])
                print("Predict angle:", steering_angle)

                if 67 <= steering_angle <= 105:
                    print("go")
                    motor_control("go", speedSet)
                elif steering_angle > 105:
                    print("right")
                    motor_control("right", 0.7)
                    #time.sleep(0.3)
                    #motor_control("go", 0.5)
                elif steering_angle < 67:
                    print("left")
                    motor_control("left", 0.7)
                    #time.sleep(0.3)
                    #motor_control("go", 0.5)

            if carState == "stop":
                motor_stop()

    except KeyboardInterrupt:
        pass

    finally:
        camera.release()
        cv2.destroyAllWindows()
        trigger_1.close()
        echo_1.close()
        trigger_2.close()
        echo_2.close()
        trigger_3.close()
        echo_3.close()

if __name__ == '__main__':
    main()
