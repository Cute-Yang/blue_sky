from math import log
import traceback
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]: %(message)s"
)


class DataWraper(object):
    def __init__(self, src: str):
        self.source_file = src
        self.search_map = {}
        self.need_field = [
            "account", "main_account_id", "account_class", "add_time", "deal_msg", "greeting_text",
            "complaint_msg", "add_msg", "nickname", "signature", "group_msg", "opentime", "wxpay_register_time",
            "id_bind_account_num", "age", "sex", "phone", "type", "quality","idcard"
        ]

    def _key_2_id(self, header_list):
        '''
        返回字段名称和其索引的映射
        '''
        n = len(header_list)
        index_list = list(range(n))
        result = dict(
            zip(header_list, index_list)
        )
        return result

    def _check(self, all_field, need_field):
        """
        Args:
        ------
        all_field:all the field name
        need_field:need filed name

        Return:
        _check_status:bool 
        _miss:string,the first miss field name
        """
        for name in need_field:
            if name not in all_field:
                return False, name
        return True, ""

    def wrap_data(self, line_split):
        """
        Args:
        ------
        line_split:split_data from source file
        """
        if not self.search_map:
            raise ValueError("search map is empty!")
        try:
            # 微信号
            account_id = self.search_map["wxid"]
            account = line_split[account_id]

            # 帐号类别,区别本帐号和扩散帐号
            account_class_id = self.search_map["account_class"]
            account_class = line_split[account_class_id]

            # 投诉记录
            complaint_msg_id = self.search_map["complaint_msg"]
            complaint_msg = line_split[complaint_msg_id]

            # add_time,任务添加时间
            add_time_id = self.search_map["add_time"]
            add_time = line_split[add_time_id]

            # deal_msg 处置信息
            deal_msg_id = self.search_map["deal_msg"]
            deal_msg = line_split[deal_msg_id]

            # greeting msg 出入账文本
            greeting_msg_id = self.search_map["greeting_text"]
            greeting_msg = line_split[greeting_msg_id]

            # add_msg 辅助证据
            add_msg_id = self.search_map["add_msg"]
            add_msg = line_split[add_msg_id]

            # nickname
            nickname_id = self.search_map["nickname"]
            nickname = line_split[nickname_id]

            # signature
            signature_id = self.search_map["signature"]
            signature = line_split[signature_id]

            # group_msg 微信群信息
            group_msg_id = self.search_map["group_msg"]
            group_msg = line_split[group_msg_id]

            # opentime 开通时间
            opentime_id = self.search_map["opentime"]
            opentime = line_split[opentime_id]

            # wxpay_register_time 微信注册开通时间
            wxpay_register_time_id = self.search_map["wxpay_register_time"]
            wxpay_register_time = line_split[wxpay_register_time_id]

            # id_bindcard_number 身份证绑卡数量
            id_bind_account_num_id = self.search_map["id_bind_account_num"]
            id_bind_account_num = line_split[id_bind_account_num_id]

            # age
            age_id = self.search_map["age"]
            age = line_split[age_id]

            quality_id = self.search_map["quality"]
            quality = line_split[quality_id]
            # phone
            phone_id = self.search_map["phone"]
            phone = line_split[phone_id]

            # sex
            sex_id = self.search_map["sex"]
            sex = line_split[sex_id]

            main_account_id = self.search_map["main_account_id"]
            main_account_id = line_split[main_account_id]

            related_type_id = self.search_map["type"]
            related_type = line_split[related_type_id]

            logindev_msg_id=self.search_map["logindev_msg"]
            logindev_msg=line_split[logindev_msg_id]
            
            idcard_id=self.search_map["idcard"]
            idcard=line_split[idcard_id]
            # return a data map
            data = {
                "account": account,
                "main_account_id": main_account_id,
                "account_class": account_class,
                "add_time": add_time,
                "deal_msg": deal_msg,
                "greeting_text": greeting_msg,
                "complaint_msg": complaint_msg,
                "add_msg": add_msg,
                "nickname": nickname,
                "signature": signature,
                "group_msg": group_msg,
                "opentime": opentime,
                "wxpay_register_time": wxpay_register_time,
                "id_bind_account_num": id_bind_account_num,
                "age": age,
                "quality": quality,
                "sex": sex,
                "phone": phone,
                "related_type": related_type,
                "logindev_msg":logindev_msg,
                "idcard":idcard
            }
        except KeyError:
            logging.error("error occured when get data", exc_info=True)
            data = {}
        return data

    def wrap_batch_data(self, sep: str = "\001"):
        """
        Args:
        ------
        sep:seperator of source file line,default is \001

        Returns:
        main_account_data:a map
        spread_account_data:list of several wraped data

        Raise:
        ValueError:if the data we need not found in source file
        """
        src_reader = open(self.source_file, mode="r", encoding="utf-8")
        header_list = src_reader.readline().strip().split(sep)

        if not self.search_map:
            self.search_map = self._key_2_id(header_list)

        check_stats, miss = self._check(header_list, self.need_field)
        if not check_stats:
            raise ValueError("%s we need,but miss in source file!" % miss)

        # initialize the first line wraped data
        second_line = src_reader.readline().strip().split('\001')
        data = self.wrap_data(second_line)
        account_class = data["account_class"]
        if account_class != "0":
            raise ValueError("we expected the first line data is from main account!\
                but the soruce file is not the correct format!")

        # a batch data should have the same main account id
        previous_account_id = data["main_account_id"]
        main_account_data = data
        spread_account_data = []
        for idx, data_line in enumerate(src_reader, start=1):
            data_line_split = data_line.strip().split("\001")
            data = self.wrap_data(data_line_split)
            account_id = data["main_account_id"]
            # it means that this is spread account data
            if account_id == previous_account_id:
                spread_account_data.append(data)
            else:
                yield main_account_data, spread_account_data
                # for the next batch
                main_account_data = data
                spread_account_data = []
                previous_account_id = account_id
            if idx % 1000 == 0:
                logging.info("already read %d rows from data!" % idx)
        src_reader.close()


# test
if __name__ == "__main__":
    # data_file = "/home/sun/桌面/account_model/data/2021-05-08#2021-05-08.txt"
    data_file="C:/Users/sunyyao/Desktop/NanGuo/xgb_model/data/2021-05-12#2021-05-12.txt"
    data_wraper = DataWraper(
        src=data_file
    )
    data_gen = data_wraper.wrap_batch_data()
    # skip None
    next(data_gen)
    count = 0
    for main_account_data, spread_account_data in data_gen:
        if count % 100 == 0:
            logging.info("main_account_id:{} wxid:{} account_class:{} spread_account_number:{}".format(main_account_data["main_account_id"], main_account_data["account"],
                                                                                                       main_account_data["account_class"], len(spread_account_data)))
        count += 1

    logging.info("TEST PASS")
