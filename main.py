import streamlit as st
from pymongo import MongoClient, DESCENDING
from datetime import datetime
now = datetime.now

health_client = MongoClient().health




def do_title():
	st.markdown("# 卡路里目标计算器")

def get_user_id():
	user_list = list(health_client.user.find({}))

	user = st.selectbox(
		label = "请选择用户",
		options = user_list,
		index = 0,
		format_func = lambda x: x["name"]
		)

	user_id = user["_id"]
	return user_id

def get_last_record(user_id):
	latest_record = health_client.calorie_target.find_one(dict(user_id=user_id), sort=[("time",DESCENDING)])
	if not latest_record:
		return dict()
	return latest_record

def log_record_time(latest_record):
	st.markdown("### 时间")
	if not latest_record:
		st.markdown("No Record")
	else:
		st.markdown(f"Last Record: {latest_record['time']}")

def kg2lb(weight):
	return weight*2.2

def input_weight(latest_record):
	weight = float(latest_record.get("weight", 100))
	st.markdown("### 体重(KG)")
	weight = st.number_input(
		label="选择值",
		min_value=float(40),
		max_value=float(120),
		value=weight,
		step=0.05
	)
	st.markdown(f"经换算，你的体重为 **{round(kg2lb(weight),2)} lbs**")
	return weight

def compute_maintenance_calorie(lb_weight, maintenance_calorie_factor):
	return lb_weight*maintenance_calorie_factor

def select_maintenance_calorie(latest_record):
	maintenance_calorie_factor = float(latest_record.get("maintenance_calorie_factor", 14))
	st.markdown("### 维持体重卡路里系数")
	maintenance_calorie_factor = st.slider(
		label="请按照情况选择系数，系数越高代表平时运动越多(14为办公室码农，16为工地搬砖佬)",
		min_value=float(14),
		max_value=float(16),
		step=0.5,
		value=maintenance_calorie_factor
	)
	st.markdown(f"您每天维持当前体重大致消耗 **{round(compute_maintenance_calorie(kg2lb(latest_record['weight']),maintenance_calorie_factor),2)} kCal**")
	return maintenance_calorie_factor

def compute_maintenance_protein(lb_weight, maintenance_protein_factor):
	return lb_weight*maintenance_protein_factor

def select_maintenance_protein(latest_record):
	maintenance_protein_factor = latest_record.get("maintenance_protein_factor", 0.8)
	st.markdown("### 维持体态蛋白质系数")
	maintenance_protein_factor = st.slider(
		label="请按照情况选择系数，系数越高代表平时运动越多(0.8为肥宅，1.3为运动狂魔)",
		min_value=0.8,
		max_value=1.3,
		step=0.1,
		value=maintenance_protein_factor
	)
	st.markdown(f"您每天维持当前体态需进食 **{round(compute_maintenance_protein(kg2lb(latest_record['weight']),maintenance_protein_factor),2)} g** 蛋白质")
	return maintenance_protein_factor

def compute_maintenance_fat(lb_weight, maintenance_fat_factor):
	return lb_weight*maintenance_fat_factor

def select_maintenance_fat(latest_record):
	maintenance_fat_factor = latest_record.get("maintenance_fat_factor", 0.3)
	st.markdown("### 维持体态脂肪系数")
	maintenance_fat_factor = st.slider(
		label="请按照情况选择系数，系数越高代表平时越爱吃脂肪(0.3为喜欢吃面食，0.4为喜欢吃高油)",
		min_value=0.3,
		max_value=0.4,
		step=0.01,
		value=maintenance_fat_factor
	)
	st.markdown(f"您每天维持当前体态需进食 **{round(compute_maintenance_fat(kg2lb(latest_record['weight']),maintenance_fat_factor),2)} g** 脂肪")
	return maintenance_fat_factor

def compute_carb(maintenance_calorie, maintenance_protein, maintenance_fat):
	st.markdown("### 维持体态所需碳水")
	carb = (maintenance_calorie - maintenance_protein*4 - maintenance_fat*9) / 4
	st.markdown(f"根据前面的数据计算，您每天维持当前体态需进食 **{round(carb,2)} g** 碳水")
	return carb

def submit(record, user_id):
	if "_id" in latest_record:
		del latest_record["_id"]
	latest_record["time"] = now()
	latest_record["user_id"] = user_id
	health_client.calorie_target.insert_one(latest_record)

do_title()

st.divider()

user_id = get_user_id()

latest_record = get_last_record(user_id)

log_record_time(latest_record)

latest_record["weight"] = input_weight(latest_record)
lb_weight = kg2lb(latest_record["weight"])

latest_record["maintenance_calorie_factor"] = select_maintenance_calorie(latest_record)
maintenance_calorie = compute_maintenance_calorie(lb_weight, latest_record["maintenance_calorie_factor"])
latest_record["maintenance_calorie"] = maintenance_calorie

latest_record["maintenance_protein_factor"] = select_maintenance_protein(latest_record)
maintenance_protein = compute_maintenance_protein(lb_weight, latest_record["maintenance_protein_factor"])
latest_record["maintenance_protein"] = maintenance_protein


latest_record["maintenance_fat_factor"] = select_maintenance_fat(latest_record)
maintenance_fat = compute_maintenance_fat(lb_weight, latest_record["maintenance_fat_factor"])
latest_record["maintenance_fat"] = maintenance_fat

latest_record["maintenance_carb"] = compute_carb(
	maintenance_calorie=maintenance_calorie,
	maintenance_protein=maintenance_protein,
	maintenance_fat=maintenance_fat
	)

st.button(
	label="提交卡路里目标",
	on_click=submit,
	kwargs=dict(
		record=latest_record,
		user_id=user_id,
		),
	use_container_width=True
	)