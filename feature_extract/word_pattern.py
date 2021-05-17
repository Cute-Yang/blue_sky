#微信群相关的正则匹配
chatroom_pattern_v1=r"麻将|金花|斗地主|牛牛|三缺一|扑克|扫雷|捕鱼|红中|血战到底|斗牛|牛群|自摸|跑得快|\
                发财|房费|体彩|彩票|信用卡|纸牌|代刷|大乐透|USDT|火币|买马|双色球|下注|打牌|麻友\
        配码|港币|港幣|兑换|澳門|澳币|澳幣|美金|葡币|美国钱|美元|葡京|缅币|日元|日币|台币|台幣|跑得快|把把清|地主|股子|群主免|兼职|返现"
chatroom_pattern_v2=r"[1-9,一,二,三,四,五,六,七,八,九,十]+[快,块,元,毛,分,米,包][1-9,一,二,三,四,五,六,七,八,九,十]+[分,点,把,个,倍]"


#出入账文本异常的正则匹配

greeting_pattern=r"麻将|金花|斗地主|牛牛|三缺一|扑克|扫雷|捕鱼|红中|血战到底|斗牛|牛群|自摸|跑得快|发财|房费|体彩|彩票|\
        信用卡|纸牌|代刷|大乐透|USDT|火币|买马|双色球|下注|打牌|麻友|配码|港币|港幣|兑换|澳門|澳币|澳幣|美金|葡币|美国钱|\
        美元|葡京|缅币|日元|日币|台币|台幣|跑得快|把把清|地主|股子|狗狗币|猪币"


#举报人收红包
reporter_redpacket_pattern=r"举报人:<appmsg start>title:微信红包 "
reporter_transfer_pattern=r"举报人:<appmsg start>title:微信转账 des:收到转账￥?\d+\.\d+?元"

#被举报人首红包
be_reported_redpacket_pattern=r"被举报人:<appmsg start>title:微信红包 "
be_reported_transfer_pattern=r"被举报人:<appmsg start>title:微信转账 des:收到转账￥?\d+\.\d+?元"


#举报涉及赌博的pattern
# |虎|兔|龙|蛇|马|羊|猴|鸡|狗|猪
gamble_evidence_pattern=r"上分|下分|斗牛|特码|房费|菠菜|埋雷|一分一毛|免死|一元三代|金砖|发包|免罚|免死|商行|金行|僵尸粉检测|送分|麻将|斗地主|跑得快"

#举报中涉及返回
cashback_evidence_pattern=r"立返红包|二维码|淘宝|下单|拼多多|京东"

#举报中涉及套现
cashout_evidence_pattern=r"套码|刷机|机佬"

#举报中设计汇兑
exchange_evidence_pattern=r"换钱|汇率|商品劵|美金|CNY|兑"

#举报中涉及色情
porn_evidence_pattern=r"上课|开课|米/课|米/次|课表|楼凤|上门|站街|新茶|喝茶|男子高校生的日常|茶艺课|🍵|快餐"

#设计拉黑
pull_back_pattern=r"拉黑|删除|删了"
porn_proof_pattern=r"黄色|淫秽|色情|小视频"

#第三方支付
third_party_pay_pattern=r"支付宝"

#国内手机号码正则
phone_pattern=r"^(\+?0?86\-?)?1[345789]\d{9}$"
