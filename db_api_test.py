import subprocess
import time
import json


url = "http://10.158.103.82:8089/fetch-data"

while True:
    try:
        # DOS의 curl 명령어를 호출합니다.
        result = subprocess.run(["curl", url], capture_output=True, text=True)

        print(f"호출 데이터  {result.stdout} ")
        data = json.loads(result.stdout)
        main_DB_ip = data["sourcePublicIp"]
        vip = data["vip"]
        main_DB_sequence_number = data["sourceSquenceNumber"]
        sub_DB_ip = data["targetPublicIp"]
        sub_DB_sequence_number = data["targetSequenceNumber"]


        print(f"VIP는 : {vip}")
        print(f"메인 DB의 IP는 : {main_DB_ip}")
        print(f"예비 DB의 IP는 : {sub_DB_ip}")

        print(f"메인 DB의 시퀀스 넘버는 {main_DB_sequence_number}")
        print(f"서브 DB의 시퀀스 넘버는 {sub_DB_sequence_number}")
        print(f"두 DB의 시퀀스 차이는 {abs(int(main_DB_sequence_number) - int(sub_DB_sequence_number))} 입니다.")

        if abs(int(main_DB_sequence_number) - int(sub_DB_sequence_number)) >5 and abs(int(main_DB_sequence_number) - int(sub_DB_sequence_number)) <10:
            print("DB시퀀스의 격차가 5~10 사이입니다. 주의하세요")
        elif abs(int(main_DB_sequence_number) - int(sub_DB_sequence_number)) >= 10:
            print("10 이상의 격차입니다. 주의하세요")
        else:
            print("DB가 잘 동기화 되고 있습니다.")


        # print(result.stdout["sourcePublicIP"])


    except Exception as e:
        print("Error occurred:", e)
    time.sleep(60)
