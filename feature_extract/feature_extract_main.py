import data_interface
import evidence_feature
import wxbasic_feature
import bg_judge_feature
import intercept_feature
import datetime

SOURCE_FILE=data_file="C:/Users/sunyyao/Desktop/NanGuo/xgb_model/data/2021-05-12#2021-05-12.txt"
DST_FILE="text.txt"
writer=open(DST_FILE,mode="w",encoding="utf-8")
TIME_FORMAT="%Y-%m-%d %H:%M:%S"
def main():
    data_wraper=data_interface.DataWraper(
        src=SOURCE_FILE
    )
    data_gen=data_wraper.wrap_batch_data()
    #skip None
    next(data_gen)
    for main_account_data,spread_account_data in data_gen:
        main_account_id=main_account_data["main_account_id"]
        wxid=main_account_data["account"]
        quality=main_account_data["quality"]
        add_time=main_account_data["add_time"]
        task_create_time=datetime.datetime.strptime(add_time,TIME_FORMAT)
        
        output=[
            main_account_id,wxid,quality
        ]

        intercept_output=intercept_feature.pase_line(
            main_account_data=main_account_data,
            task_create_time=task_create_time
        )
        evidence_output=evidence_feature.parse_line(
            main_account_data=main_account_data,
            spread_account_data=spread_account_data,
            task_create_time=task_create_time
        )
        wxbasic_output=wxbasic_feature.parse_line(
            main_account_data=main_account_data,
            spread_account_data=spread_account_data,
            task_create_time=task_create_time
        )
        bg_judge_output=bg_judge_feature.parse_line(
            main_account_data=main_account_data
        )

        #这里可以ignore，或者也可以自己添加默认数据
        if intercept_output and evidence_output and wxbasic_output and bg_judge_output:
            output.extend(intercept_output)
            output.extend(evidence_output)
            output.extend(wxbasic_output)
            output.extend(bg_judge_output)
            
            output=[str(item) for item in output]
            write_string="\001".join(output)
            writer.write(write_string)
            writer.write("\n")
    writer.close()

if __name__=="__main__":
    main()