from fpdf import FPDF

class ZhiyunPDF(FPDF):
    def header(self):
        self.set_font("SimHei", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "智云科技 ZHIYUN TECH", align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("SimHei", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"第 {self.page_no()}/{{nb}} 页  |  机密文件 - 仅供内部使用", align="C")

    def chapter_title(self, title):
        self.set_font("SimHei", "B", 16)
        self.set_text_color(0, 102, 204)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def section_title(self, title):
        self.set_font("SimHei", "B", 13)
        self.set_text_color(51, 51, 51)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def sub_title(self, title):
        self.set_font("SimHei", "B", 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("SimHei", "", 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("SimHei", "", 10)
        self.set_text_color(51, 51, 51)
        self.cell(8, 6, "•")
        self.multi_cell(0, 6, text)
        self.ln(1)

    def table_row(self, cells, widths, bold=False):
        style = "B" if bold else ""
        self.set_font("SimHei", style, 9)
        self.set_text_color(51, 51, 51)
        h = 7
        for i, cell in enumerate(cells):
            self.cell(widths[i], h, str(cell), border=1, align="C" if i > 0 else "L")
        self.ln(h)

    def table_header(self, cells, widths):
        self.set_fill_color(0, 102, 204)
        self.set_text_color(255, 255, 255)
        self.set_font("SimHei", "B", 9)
        h = 7
        for i, cell in enumerate(cells):
            self.cell(widths[i], h, str(cell), border=1, fill=True, align="C")
        self.ln(h)


pdf = ZhiyunPDF()
pdf.alias_nb_pages()
pdf.add_font("SimHei", "", "C:/Windows/Fonts/simhei.ttf")
pdf.add_font("SimHei", "B", "C:/Windows/Fonts/simhei.ttf")

# ==================== PDF 1: 产品发布报告 ====================
pdf.add_page()
pdf.chapter_title("智云科技 2025 年 Q1 产品发布报告")
pdf.body_text("报告日期：2025年4月15日\n编制部门：产品管理部\n审核人：张明（产品VP）")

pdf.section_title("一、执行摘要")
pdf.body_text("2025年第一季度，智云科技共发布 3 款新品，完成 2 款产品的重大升级。新品总销量达到 12,800 台，超额完成季度目标 128%。灵犀大模型 v2.5 的上线显著提升了全系产品的用户体验，用户满意度从 4.2 分提升至 4.6 分（5分制）。")

pdf.section_title("二、新品发布详情")
pdf.sub_title("2.1 智云音箱 Pro（ZY-SP100）")
pdf.bullet("发布日期：2025年3月15日")
pdf.bullet("官方售价：899元（首发优惠价699元）")
pdf.bullet("首月销量：5,200台，超出预期 173%")
pdf.bullet("核心卖点：灵犀大模型 v2.5、6麦克风远场拾音、Wi-Fi 6")
pdf.bullet("用户好评率：96.3%")

pdf.sub_title("2.2 智云智能猫眼（ZY-PE100）")
pdf.bullet("发布日期：2025年4月10日")
pdf.bullet("官方售价：899元")
pdf.bullet("首周预订量：1,200台")
pdf.bullet("核心卖点：180°超广角、AI访客识别、远程可视对讲")

pdf.sub_title("2.3 智云智能晾衣架（ZY-DR100）")
pdf.bullet("发布日期：2025年4月1日")
pdf.bullet("官方售价：1,999元")
pdf.bullet("首月销量：380台（新品导入期，符合预期）")
pdf.bullet("核心卖点：风干+烘干双模式、语音控制、LED照明")

pdf.section_title("三、销售数据分析")
w = [30, 50, 25, 25, 25, 25]
pdf.table_header(["产品", "型号", "售价(元)", "销量", "收入(万)", "占比"], w)
pdf.table_row(["音箱Pro", "ZY-SP100", "899", "5,200", "467.5", "36.5%"], w)
pdf.table_row(["安防S2套装", "ZY-CV200-KIT", "899", "3,200", "287.7", "22.5%"], w)
pdf.table_row(["安防S2单机", "ZY-CV200", "499", "2,800", "139.7", "10.9%"], w)
pdf.table_row(["中控屏", "ZY-CP100", "1299", "920", "119.5", "9.3%"], w)
pdf.table_row(["智能门锁L2", "ZY-DL200", "1599", "650", "103.9", "8.1%"], w)
pdf.table_row(["其他", "—", "—", "—", "161.7", "12.6%"], w)

pdf.section_title("四、关键指标对比")
pdf.sub_title("同比增长（Q1 2025 vs Q1 2024）")
pdf.bullet("总营收：1,280万元 → 1,280万元（+42%）")
pdf.bullet("新品首发销量：4,600台 → 12,800台（+178%）")
pdf.bullet("用户满意度：4.2 → 4.6（+9.5%）")
pdf.bullet("NPS（净推荐值）：32 → 48（+50%）")
pdf.bullet("退货率：3.8% → 1.9%（-50%）")

pdf.section_title("五、问题与风险")
pdf.bullet("供应链风险：Zigbee 3.0 芯片交期延长至 16 周，需提前备货")
pdf.bullet("竞品压力：竞品A 发布同价位智能音箱，价格战可能加剧")
pdf.bullet("售后压力：智能晾衣架安装复杂度高，售后工单量超出预期 2 倍")

pdf.section_title("六、Q2 计划")
pdf.bullet("5月：灵犀大模型 v2.6 OTA 推送（多语言支持）")
pdf.bullet("6月：智云智能窗帘电机 Pro 发布（静音升级+ Matter 2.0）")
pdf.bullet("6月：开放平台 v3 上线（Agent 工具调用接口）")

pdf.output("D:/code/RAG/data/pdf/product_launch_report_q1_2025.pdf")

# ==================== PDF 2: 用户调研报告 ====================
pdf = ZhiyunPDF()
pdf.alias_nb_pages()
pdf.add_font("SimHei", "", "C:/Windows/Fonts/simhei.ttf")
pdf.add_font("SimHei", "B", "C:/Windows/Fonts/simhei.ttf")

pdf.add_page()
pdf.chapter_title("智云科技 智能家居用户调研报告")
pdf.body_text("调研时间：2025年3月1日 - 3月31日\n样本量：2,000 名智云活跃用户\n执行团队：用户研究部\n报告版本：v1.0")

pdf.section_title("一、调研背景与目标")
pdf.body_text("为更好地了解用户对智云智能家居产品的真实使用感受和需求，我们在2025年3月开展了大规模用户调研。本次调研覆盖全国28个省市，样本涵盖一线城市（40%）、新一线城市（35%）和二三线城市（25%）。")

pdf.body_text("核心目标：\n1. 评估现有产品的用户满意度和痛点\n2. 挖掘未被满足的用户需求\n3. 了解用户对竞品的认知和态度\n4. 为下一代产品规划提供数据支撑")

pdf.section_title("二、用户画像")
pdf.sub_title("2.1 基本信息")
pdf.bullet("年龄分布：25-35岁（48%）、36-45岁（32%）、18-24岁（12%）、46岁以上（8%）")
pdf.bullet("家庭结构：三口之家（42%）、二人世界（28%）、独居（18%）、三代同堂（12%）")
pdf.bullet("月收入分布：1-2万（45%）、2-3万（28%）、5千-1万（18%）、3万以上（9%）")
pdf.bullet("科技爱好者占比：67%（定义：会主动关注科技产品评测）")

pdf.sub_title("2.2 智云产品使用情况")
pdf.bullet("平均拥有智云设备数量：6.3 台")
pdf.bullet("使用智云产品超过1年的用户占比：58%")
pdf.bullet("使用过智能场景功能的用户占比：72%")
pdf.bullet("使用过语音控制的用户占比：89%")

pdf.section_title("三、满意度分析")
pdf.sub_title("3.1 各产品满意度评分（5分制）")

w2 = [60, 30, 30, 60]
pdf.table_header(["产品", "评分", "样本", "主要好评点"], w2)
pdf.table_row(["音箱Pro", "4.7", "856", "音质好、AI对话自然"], w2)
pdf.table_row(["安防摄像头S2", "4.5", "623", "画质清晰、AI识别准"], w2)
pdf.table_row(["中控屏", "4.4", "312", "操作流畅、功能全"], w2)
pdf.table_row(["智能门锁L2", "4.3", "289", "指纹快、安全"], w2)
pdf.table_row(["智能灯泡L1", "4.2", "1,024", "性价比高"], w2)
pdf.table_row(["智能插座P1", "4.1", "1,456", "便宜好用"], w2)

pdf.sub_title("3.2 最常被提及的痛点 TOP 5")
pdf.bullet("APP 偶尔卡顿（被提及 342 次，17.1%）")
pdf.bullet("设备偶尔离线需重新配对（被提及 278 次，13.9%）")
pdf.bullet("智能场景执行偶尔有延迟（被提及 256 次，12.8%）")
pdf.bullet("新品安装说明不够详细（被提及 189 次，9.5%）")
pdf.bullet("希望支持更多第三方品牌设备（被提及 167 次，8.4%）")

pdf.section_title("四、用户需求洞察")
pdf.sub_title("4.1 最期待的新功能 TOP 5")
pdf.bullet("1. 更好的离线语音能力（72% 用户表示非常需要）")
pdf.bullet("2. 家庭成员个性化推荐（65%）")
pdf.bullet("3. 能耗分析和节能建议（58%）")
pdf.bullet("4. 宠物监测和互动（45%）")
pdf.bullet("5. 与新能源汽车联动（如回家前预开空调）（42%）")

pdf.sub_title("4.2 竞品认知")
pdf.bullet("56% 的用户同时使用其他品牌智能设备")
pdf.bullet("最常搭配使用的竞品品牌：小米（38%）、华为（22%）、苹果HomeKit（15%）")
pdf.bullet("用户选择智云的首要原因：AI对话体验（41%）、安防产品线完整（28%）")
pdf.bullet("用户考虑更换的首要原因：生态不够开放（32%）、价格偏高（25%）")

pdf.section_title("五、关键建议")
pdf.bullet("优先级1：优化APP性能和设备连接稳定性（影响 31% 用户体验）")
pdf.bullet("优先级2：加强 Matter 生态建设，提升第三方设备兼容性")
pdf.bullet("优先级3：开发能耗分析功能，与绿色智能概念结合")
pdf.bullet("优先级4：改善安装说明文档质量，增加视频教程")
pdf.bullet("优先级5：探索新能源汽车/IoT 联动场景")

pdf.output("D:/code/RAG/data/pdf/user_research_report_2025q1.pdf")

# ==================== PDF 3: API 使用说明书 ====================
pdf = ZhiyunPDF()
pdf.alias_nb_pages()
pdf.add_font("SimHei", "", "C:/Windows/Fonts/simhei.ttf")
pdf.add_font("SimHei", "B", "C:/Windows/Fonts/simhei.ttf")

pdf.add_page()
pdf.chapter_title("智云开放平台 API 使用说明书")
pdf.body_text("版本：v2.3\n适用对象：第三方开发者、合作伙伴\n文档密级：公开")

pdf.section_title("一、概述")
pdf.body_text("智云开放平台提供 RESTful API，允许第三方开发者接入智云智能家居生态，实现设备控制、场景管理、数据查询等功能。所有 API 均采用 OAuth 2.0 认证，支持 JSON 格式请求和响应。")

pdf.sub_title("1.1 系统要求")
pdf.bullet("注册智云开放平台开发者账号")
pdf.bullet("创建应用并获取 app_id 和 app_secret")
pdf.bullet("具备基本的 HTTP/REST API 开发能力")
pdf.bullet("服务器支持 HTTPS（TLS 1.2+）")

pdf.sub_title("1.2 API 概览")
w3 = [50, 60, 80]
pdf.table_header(["模块", "端点前缀", "功能说明"], w3)
pdf.table_row(["认证", "/auth/token", "获取和刷新访问令牌"], w3)
pdf.table_row(["设备", "/devices", "设备列表/控制/历史数据"], w3)
pdf.table_row(["场景", "/scenes", "场景创建/执行/管理"], w3)
pdf.table_row(["语音", "/voice", "ASR/NLU/对话管理"], w3)
pdf.table_row(["用户", "/users", "用户信息/偏好管理"], w3)
pdf.table_row(["告警", "/alerts", "安防告警/通知管理"], w3)

pdf.section_title("二、快速入门")
pdf.sub_title("2.1 获取访问令牌")
pdf.body_text('请求：\nPOST /v2/auth/token\nContent-Type: application/json\n\n{"app_id": "cli_abc123", "app_secret": "sk_xyz789", "grant_type": "client_credentials"}')
pdf.body_text('响应：\n{"access_token": "eyJhbGci...", "token_type": "Bearer", "expires_in": 7200}')

pdf.sub_title("2.2 查询设备列表")
pdf.body_text('请求：\nGET /v2/devices?page=1&page_size=10\nAuthorization: Bearer eyJhbGci...')
pdf.body_text('响应：\n{"total": 15, "devices": [{"device_id": "ZY-SP100-001", "name": "客厅音箱", "online": true}]}')

pdf.sub_title("2.3 控制设备")
pdf.body_text('请求：\nPOST /v2/devices/ZY-LT100-001/command\n{"command": "set_property", "params": {"brightness": 80}}')

pdf.section_title("三、最佳实践")
pdf.bullet("令牌管理：access_token 有效期 2 小时，建议在过期前 5 分钟自动刷新")
pdf.bullet("错误重试：遇到 429（限流）或 5xx 错误时，使用指数退避策略重试（最多 3 次）")
pdf.bullet("批量操作：尽量使用 batch_command 接口，减少 API 调用次数")
pdf.bullet("数据缓存：设备状态等频繁查询的数据建议本地缓存 30 秒")
pdf.bullet("Webhook：对于实时性要求高的场景（如安防告警），使用 Webhook 推送而非轮询")

pdf.section_title("四、错误处理")
w4 = [25, 50, 60, 55]
pdf.table_header(["错误码", "含义", "原因", "处理建议"], w4)
pdf.table_row(["401", "未授权", "Token无效/过期", "重新获取Token"], w4)
pdf.table_row(["403", "禁止访问", "无设备权限", "确认设备绑定"], w4)
pdf.table_row(["404", "未找到", "资源不存在", "检查ID"], w4)
pdf.table_row(["429", "请求过多", "超出限流", "降低频率/等待"], w4)
pdf.table_row(["500", "服务器错误", "内部异常", "稍后重试"], w4)

pdf.section_title("五、安全建议")
pdf.bullet("app_secret 不要硬编码在客户端代码中，应存放在服务端环境变量中")
pdf.bullet("定期轮换 app_secret（建议每 90 天）")
pdf.bullet("使用 IP 白名单限制 API 访问来源")
pdf.bullet("敏感操作（如删除设备）建议增加二次确认机制")
pdf.bullet("所有 API 请求必须通过 HTTPS，禁止使用 HTTP")

pdf.output("D:/code/RAG/data/pdf/api_user_guide.pdf")

print("All 3 PDF files generated successfully!")
