from flask import Flask,request,jsonify
from sqlalchemy.exc import IntegrityError
import redis
from flaskAssignment import app,bcrypt,db
#from flaskAssignment.model import teacher,student,course,post
import jwt
from datetime import timedelta,datetime,timezone
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import pandas
from flaskAssignment.model import Subject,User,Department,Role,Post,Profile,TokenBlocklist,TeacherSubject,Tag
from sqlalchemy import or_,and_
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity,get_jwt
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
ACCESS_EXPIRES = timedelta(hours=1)
jwt = JWTManager(app)
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()

    return token is not None
@app.route("/logout", methods=["DELETE"])
@jwt_required()
def modify_token():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()
    return jsonify(msg="JWT revoked")

@app.route("/",methods=['GET'])
@jwt_required()
def default():
    current_user = get_jwt_identity()
    return current_user
    return jsonify(logged_in_as=current_user)
@app.route("/login",methods=['POST'])
def login():
     email = request.form.get("email")
     password = request.form.get("password")
     my_user = User.query.filter_by(email=email).first()
     if (my_user!=None) and (bcrypt.check_password_hash(my_user.password,password)) :
         access_token = str(create_access_token(identity=int(my_user.id)))
         my_user._is_login_=True
         db.session.commit()
         return jsonify(access_token=access_token,user_id=my_user.id)
     else:
          return jsonify({"msg": "Bad username or password"}), 401
@app.route("/register",methods=['POST'])
def register():
    email = request.form.get("email")
    name = request.form.get("name")
    password = request.form.get("password")
    user_id = request.form.get("user_id")
    role_id=request.form.get("role_id")
    department_id = request.form.get("department_id")
    my_student = db.session.query(User).filter(or_(User.user_id==user_id,User.email==email)).first()
    my_department = Department.query.filter_by(id=department_id).first()
    my_role=Role.query.filter_by(id=role_id)
    if my_student!=None :
         return "User already registered ! Please Login!!"
    elif my_department==None:
         return "The course is not exist ! Please Insert the valid CourseID!"
    elif my_department==None:
         return "The role is not exist ! Please Insert the valid role id!"
    else:
       my_user=User(email=email,name=name,password=bcrypt.generate_password_hash(password,10).decode('utf-8'),user_id=user_id,department_id=int(department_id),role_id=int(role_id))
       db.session.add(my_user)
       db.session.commit()
       my_profile = Profile(user=my_user,department=my_department.department_name,user_name=my_user.name,email=my_user.email)
       db.session.add(my_profile)
       db.session.commit()
       return "Success"
@app.route("/view_profile/<int:User_id>",methods=['GET'])
@jwt_required()
def view_profile(User_id):
    current_user=get_jwt_identity()
    my_profile = Profile.query.filter_by(user_id=User_id).first()
    if my_profile !=None and current_user==my_profile.user_id:
        data={
            "user_id":my_profile.user_id,
            "user_name":my_profile.user_name,
            "email":my_profile.email,
            "department":my_profile.department,
            "nationality":my_profile.nationality
        }
        return data
    else:
        return "No Authority!"
@app.route("/edit_profile/<int:user_id>",methods=['PATCH'])
@jwt_required()
def edit_profile(user_id):
    current_user=get_jwt_identity()
    my_profile = Profile.query.filter_by(user_id=user_id).first()
    if my_profile !=None and current_user==my_profile.id:
        my_profile.user_name=request.form.get('user_name')
        my_profile.nationality=request.form.get('nationality')
        my_profile.dateofbirth=datetime.strptime(request.form.get("dob"),"%d/%m/%y")
        my_profile.phonenumber=request.form.get('phonenumber')
        db.session.commit()
        return "Success"
    else:
        return "No Authority!"
@app.route("/post",methods=['POST'])
@jwt_required()
def my_post():
    assignment_name=request.form.get("assignment_name")
    assignment_content=request.form.get("assignment_content")
    maximium_score = int(request.form.get("score"))
    remark = request.form.get("remark")
    deadline = datetime.strptime(request.form.get("deadline"),"%d/%m/%y %H:%M:%S")
    subject_id=int(request.form.get("subject_id"))
    current_user = get_jwt_identity()
    my_user = User.query.filter_by(id=current_user).first()
    tags = request.form.get("tags")
    #my_subject=Subject.query.filter_by(id=subject_id).first()
    my_teacher_sub=TeacherSubject.query.filter_by(teacher_id=current_user).first()
    if my_user.role.role_name=='Teacher':
       if my_teacher_sub==None:
           return "Teacher hanvent registered!"
       elif my_teacher_sub!=None and my_teacher_sub.department_id==my_user.department_id:
         my_post= Post(assignment_titile=assignment_name+"("+str(my_teacher_sub.subject.subject_name)+")",assignment_content=assignment_content,maximium_score=maximium_score,remark=remark,deadline=deadline,posted_by=my_user.id, subject_id=subject_id)
         db.session.add(my_post)
         new_tage_list=tags.split(" ")
         for i in range(0,len(new_tage_list)):
             tag=Tag(name=new_tage_list[i])
             my_post.tags.append(tag)
         db.session.commit()
         return "Sucessful Post"
       else:
           return "Unauthorized"
    else:
        return "No authority!"

@app.route("/view_post",methods=['GET'])
@jwt_required()
def view_post():
    my_post=Post.query.all()
    if my_post!=None:
     post_list=[]
     tag_list=[]
     for i in my_post:
        for j in i.tags:
            tag_list.append(j.name)
        data={
            "post_id":i.id,
            "post_title":i.assignment_titile,
            "author":i.posted_by,
            "assignment_content":i.assignment_content,
            " maximium_score":i.maximium_score,
            "remark":i.remark,
            "date_posted":i.date_posted,
            " deadline":i. deadline,
            "tags":tag_list
        }
        post_list.append(data)
     return post_list
    else:
        return "Post is not exist!"
@app.route("/delete_post/<string:post_id>",methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
     current_user = get_jwt_identity()
     my_user = User.query.filter_by(id=current_user).first()
     my_post=Post.query.filter_by(id=post_id).first()
     if my_post!=None:
       if my_user.role.role_name=='Teacher' and my_post.posted_by==my_user.id:
            db.session.delete(my_post)
            db.session.commit()
            return "Post Deleted !"
       else:
            return "No Authority"
     else:
         return "Post is not exist!"       
@app.route("/update_post/<string:post_id>",methods=['GET','PATCH'])
@jwt_required()
def update_post(post_id):
     my_post=Post.query.filter_by(id=post_id).first()
     assignment_content=request.form.get("assignment_content")
     maximium_score = request.form.get("score")
     remark = request.form.get("remark")
     deadline = datetime.strptime(request.form.get("deadline"),"%d/%m/%y %H:%M:%S")
     subject_id=int(request.form.get("subject_id"))
     current_user = get_jwt_identity()
     my_user = User.query.filter_by(id=current_user).first()
     my_subject=Subject.query.filter_by(id=subject_id).first()
     if my_post!=None and my_user.role.role_name=='Teacher' and my_subject!=None and my_post.posted_by==my_user.id:
         my_post.assignment_content=assignment_content
         my_post.maximium_score=maximium_score
         my_post.remark=remark
         my_post.deadline=deadline
         my_post.subject_id=subject_id
         db.session.commit()
         return "Successful"
     else:
          return "No Authority"
@app.route("/register_csv",methods=['POST'])
def register_csv():
    file = request.files["file_name"]
    filename = secure_filename(file.filename)
    data = pandas.read_csv(filename)
    student_id_list=list(data["student_id"].tolist())
    student_email_list=list(data["student_email"].tolist())
    student_name_list=list(data["student_name"].tolist())
    department_id_list=list(data["department_id"].tolist())
    password_list=list(data["password"].tolist())
    role_id_list=list(data["role_id"].tolist())
    student_data_list=[]
    for i in range(0,len(list(student_id_list))):
        student_data = {
             "email":student_email_list[i],
             "name":student_name_list[i],
             "student_id":student_id_list[i],
             "password":bcrypt.generate_password_hash(password_list[i],10).decode('utf-8'),
             "department_id":department_id_list[i],
             "role_id":role_id_list[i]
          }
        student_data_list.append(student_data)
    for j in range(0,len(student_data_list)):
        my_student = db.session.query(User).filter(or_(User.user_id==student_data_list[j]["student_id"],User.email==student_data_list[j]["email"])).first()
        my_department = Department.query.filter_by(id=student_data_list[j]['department_id']).first()
        # try:
        #   my_user=User(email=student_data_list[j]["email"],name=student_data_list[j]["name"],password=bcrypt.generate_password_hash(student_data_list[j]["password"]).decode('utf-8'),user_id=student_data_list[j]["student_id"],department_id=student_data_list[j]['department_id'],role_id=int(student_data_list[j]["role_id"]))
        #   db.session.add(my_user)
        #   db.session.commit()
        #   my_profile = Profile(user=my_user,department=my_department.department_name,user_name=my_user.name,email=my_user.email)
        #   db.session.add(my_profile)
        #   db.session.commit()
        # except IntegrityError:
        #     db.session.rollback()
        if my_student==None and my_department!=None:
            try:
               my_user=User(email=student_data_list[j]["email"],name=student_data_list[j]["name"],password=student_data_list[j]["password"],user_id=student_data_list[j]["student_id"],department_id=student_data_list[j]['department_id'],role_id=int(student_data_list[j]["role_id"]))
               db.session.add(my_user)
               db.session.commit()
               my_profile = Profile(user=my_user,department=my_department.department_name,user_name=my_user.name,email=my_user.email)
               db.session.add(my_profile)
               db.session.commit()
            except IntegrityError:
               db.session.rollback()
    return "Success"
@app.route("/teacher_subject_registration",methods=['POST'])
@jwt_required()
def teacher_subject_registration():
    current_user=get_jwt_identity()
    my_user = User.query.filter_by(id=current_user).first()
    my_department_id=request.form.get("department_id")
    subject_name=request.form.get("subject_name")
    my_subject=Subject.query.filter_by(subject_name=subject_name).first()
    my_teacher_sub=TeacherSubject.query.filter_by(teacher_id=current_user).first()
    if my_teacher_sub!=None and my_user!=None and my_subject!=None and my_user.role.role_name=="Teacher" and my_user.department_id==int(my_department_id) and my_subject.department_id==int(my_department_id) :
        my_res=TeacherSubject(subject_id=my_subject.id,department_id=my_department_id,user=my_user)
        db.session.add(my_res)
        db.session.commit()
        return "Successs"
    else:
        return "Unauthorized!"


# @app.route("/post",methods=['POST'])
# @app.route("/register",methods=['POST'])
# def register():
#     student_email = request.form.get("email")
#     student_name = request.form.get("student_name")
#     password = request.form.get("password")
#     student_id = request.form.get("student_id")
#     course_id = request.form.get("course_id")
#     my_student = student.find_one({'$or':[{'email':student_email},{'student_id':student_id}]})
#     my_course = course.find_one({'course_id':course_id})
#     if my_student!=None :
#         return "Student already registered ! Please Login!!"
#     elif my_course==None:
#         return "The course is not exist ! Please Insert the valid CourseID!"
#     else:
#           subject=[]
#           for i in range(0,len(my_course["subject"])):
#             subject.append({"subject_name":my_course["subject"][i],"score":0})
#           student_data = {
#             "email":student_email,
#             "name":student_name,
#             "student_id":student_id,
#             "password":bcrypt.generate_password_hash(password).decode('utf-8'),
#             "course_id":course_id,
#             "course_name":my_course["course_name"],
#             "average_score":0,
#             "grade":"",
#             "subject":subject
#         }
#           student.insert_one(student_data)
#     return "Successful Register! Congratulation"
# @app.route("/post",methods=['POST'])
# @app.route("/register",methods=['POST'])
# def register():
#     student_email = request.form.get("email")
#     student_name = request.form.get("student_name")
#     password = request.form.get("password")
#     student_id = request.form.get("student_id")
#     course_id = request.form.get("course_id")
#     my_student = student.find_one({'$or':[{'email':student_email},{'student_id':student_id}]})
#     my_course = course.find_one({'course_id':course_id})
#     if my_student!=None :
#         return "Student already registered ! Please Login!!"
#     elif my_course==None:
#         return "The course is not exist ! Please Insert the valid CourseID!"
#     else:
#           subject=[]
#           for i in range(0,len(my_course["subject"])):
#             subject.append({"subject_name":my_course["subject"][i],"score":0})
#           student_data = {
#             "email":student_email,
#             "name":student_name,
#             "student_id":student_id,
#             "password":bcrypt.generate_password_hash(password).decode('utf-8'),
#             "course_id":course_id,
#             "course_name":my_course["course_name"],
#             "average_score":0,
#             "grade":"",
#             "subject":subject
#         }
#           student.insert_one(student_data)
#     return "Successful Register! Congratulation"


# @app.route("/logout", methods=["DELETE"])
# @jwt_required()
# def logout():
#     jti = get_jwt()["jti"]
#     jwt_redis_blocklist.set(jti, "", ex=ACCESS_EXPIRES)
#     return jsonify(msg="Access token revoked")
# @app.route("/login",methods=['POST'])
# def login():
#     email = request.form.get("email")
#     password = request.form.get("password")
#     my_teacher = teacher.find_one({"email":email})
#     my_student = student.find_one({"email":email})
#     if (my_teacher!=None) and (my_teacher["password"]==password) :
#         session['logged_in']=True
#         session['role']="teacher"
#         session['user_id']=str(my_teacher["id"])
#         token = jwt.encode({
#              'user':str(my_teacher["name"]),
#              'expiration':str(datetime.utcnow()+timedelta(seconds=12000))
#             },
#             app.config['SECRET_KEY'])
#         session['token']=token.decode('utf-8')
#         return jsonify({'session':session})
#     elif (my_student!=None) and bcrypt.check_password_hash(my_student["password"],password):
#          session['logged_in']=True
#          session['role']="student"
#          session['user_id']=str(my_student["student_id"])
#          token = jwt.encode({
#              'user':my_student["name"],
#              'expiration':str(datetime.utcnow()+timedelta(seconds=12000))
#          },app.config['SECRET_KEY'])
#          session['token']=token.decode('utf-8')
#          return jsonify({'session':session})
#     else:
#         return "Please Register first"
# @app.route("/post",methods=['POST'])
# def my_post():
#     header_token=request.headers.get("Authorization")
#     assignment_name=request.form.get("assignment_name")
#     assignment_content=request.form.get("assignment_content")
#     maximium_score = request.form.get("score")
#     remark = request.form.get("remark")
#     deadline = datetime.strptime(request.form.get("deadline"),"%d/%m/%y %H:%M:%S")
#     date_posted = datetime.now().strftime("%d %m %Y %H:%M:%S")
#     if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#     else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token'] and session['role']=="teacher" :
#           my_teacher = teacher.find_one({"id":session['user_id']})
#           assignment_data = {
              
#               "posted_by":my_teacher['name'],
#               "date_posted":date_posted,
#               "subject":my_teacher['subject'],
#               "assignment_name":"2023_"+my_teacher['subject']+"_"+assignment_name,
#               "assignment_content":assignment_content,
#               "score":int(maximium_score),
#              "deadline":deadline,
#               "remark":remark
#           }
#           if my_teacher!=None or post.find_one:
#              id=post.insert_one(assignment_data).inserted_id
#              teacher.update_one({"id":session["user_id"]},{'$push':{'assignment_posted':str(id)}})
#              return "Post added! Your Post ID is "+":"+str(id)
#           else:
#              return "No authority Please Log in!"
#        else:
#            return "No authority Please Log in!"
# @app.route("/view_post",methods=["GET"])
# def view_post():
#      header_token = request.headers.get("Authorization")
#      all_post = post.find()
#      post_list=[]
#      if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#      else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token']:
#          for i in all_post:
#              post_data={
#                  "id":str(i["_id"]),
#                  "subject":i["subject"],
#                  "assignment_name":i["assignment_name"],
#                  "assignment_content":i["assignment_content"],
#                  "score":i["score"],
#                  "deadline":i["deadline"],
#                  "remark":i["remark"]
#              }
#              post_list.append(post_data)
#          return post_list
#        else:
#          return "No Authority"
# @app.route("/view_post/<string:post_id>")
# def view_post_id_based(post_id):
#     header_token = request.headers.get("Authorization")
#     if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#     else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token']:
#                 i= post.find_one({"_id":ObjectId(post_id)})
#                 if i!=None:
#                  post_data={
#                   "id":str(i["_id"]),
#                   "subject":i["subject"],
#                   "assignment_name":i["assignment_name"],
#                   "assignment_content":i["assignment_content"],
#                   "score":i["score"],
#                   "deadline":i["deadline"],
#                   "remark":i["remark"]
#                   }
#                  return post_data
#                 else:
#                  return "Post is not exist"
#        else:
#          return "No Authority"
# @app.route("/delete_post/<string:post_id>",methods=['DELETE'])
# def delete_post(post_id):
#     header_token = request.headers.get("Authorization")
#     if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#     else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token'] and session['role']=="teacher":
#                 my_teacher = teacher.find_one({'id':session['user_id']})
#                 i= post.find_one({"_id":ObjectId(post_id)})
#                 if i!=None and my_teacher['subject']==i['subject']:
#                    teacher.update_one({"id":session["user_id"]},{'$pull':{'assignment_posted':post_id}})
#                    post.delete_one({"_id":ObjectId(post_id)})
#                    return "Post is Deleted"
#                 else:
#                    return "Post is not exist"
#        else:
#          return "No Authority"
# @app.route("/update_post/<string:post_id>",methods=['PATCH'])
# def update_post(post_id):
#     header_token = request.headers.get("Authorization")
#     assignment_name=request.form.get("assignment_name")
#     assignment_content=request.form.get("assignment_content")
#     maximium_score = request.form.get("score")
#     remark = request.form.get("remark")
#     deadline = datetime.strptime(request.form.get("deadline"),"%d/%m/%y %H:%M:%S")
#     if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#     else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token'] and session['role']=="teacher":
#                 my_teacher = teacher.find_one({'id':session['user_id']})
#                 i= post.find_one({"_id":ObjectId(post_id)})
#                 if i!=None and (my_teacher['subject']==i['subject']):
#                    post.update_one({"_id":ObjectId(post_id)},{'$set':{"assignment_name":"2023_"+my_teacher['subject']+"_"+assignment_name,"assignment_content":assignment_content, "score":int(maximium_score),"deadline":deadline,"remark":remark}})
#                    return "Post is Updated!"
#                 else:
#                    return "Post is not exist"
#        else:
#          return "No Authority"
# @app.route("/update_score/<string:stu_id>",methods=['PATCH'])
# def update_score(stu_id):
#     header_token = request.headers.get("Authorization")
#     if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#     else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token'] and session['role']=="teacher":
#           my_teacher = teacher.find_one({'id':session['user_id']})
#           teacher_course_name=[]
#           for i in my_teacher["course"]:
#             teacher_course_name.append(i)
#           my_student = student.find_one({'student_id':str(stu_id)})
#           if my_student!=None and my_teacher!=None:
#               course_status=False
#               for i in range(0,len(teacher_course_name)):
#                   if teacher_course_name[i]==my_student["course_name"]:
#                       course_status=True
#               if course_status:
#                  subject_status=False
#                  course_subjects_list=[]
#                  my_course = course.find_one({'course_name':my_student["course_name"]})
#                  for i in my_course["subject"]:
#                      course_subjects_list.append(i)
#                  for k in range(0,len(course_subjects_list)):
#                      if course_subjects_list[k]==my_teacher["subject"]:
#                          subject_status=True
#                  if subject_status:
#                      score=int(request.form.get("score"))
#                      #student.update_one({'student_id':stu_id},{'$set':{'subject.$':{'subject_name':my_teacher["subject"],'score':score}}})
#                      student.update_one({'$and':[{'student_id':stu_id},{'subject.subject_name':my_teacher["subject"]}]},{'$set':{'subject.$.score':int(score)}})
#                      my_student = student.find_one({'student_id':stu_id})
#                      score_list =[]
#                      for i in my_student["subject"]:
#                          score_list.append(int(i["score"]))
#                      total_score=0
#                      grade=""
#                      for j in range(0,len(score_list)):
#                          total_score=total_score+int(score_list[j])
#                      total_score=total_score/5
#                      if total_score>=85:
#                          grade="A"
#                      elif total_score<85 and total_score>=75:
#                          grade="B"
#                      elif total_score<75 and total_score>=60:
#                          grade="C"
#                      elif total_score<60 and total_score>=55:
#                          grade="Make Up Exam"
#                      else:
#                          grade="F"
#                      student.update_one({'student_id':stu_id},{'$set':{'average_score':total_score,'grade':grade}})
#                      return "Update Sucessful"
#                  else:
#                      return "Subject is not exist"
#               else:
#                   return "Course is not exist"
#           else:
#               return "Error"
#        else:
#            return "No Authority"
# @app.route("/update_score/<string:stu_id>",methods=['PATCH'])
# def update_score(stu_id):
#     header_token = request.headers.get("Authorization")
#     if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#     else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token'] and session['role']=="teacher":
#           my_teacher = teacher.find_one({'id':session['user_id']})
#           teacher_course_name=[]
#           for i in my_teacher["course"]:
#             teacher_course_name.append(i)
#           my_student = student.find_one({'student_id':str(stu_id)})
#           if my_student!=None and my_teacher!=None:
#               course_status=False
#               for i in range(0,len(teacher_course_name)):
#                   if teacher_course_name[i]==my_student["course_name"]:
#                       course_status=True
#               if course_status:
#                  subject_status=False
#                  course_subjects_list=[]
#                  my_course = course.find_one({'course_name':my_student["course_name"]})
#                  for i in my_course["subject"]:
#                      course_subjects_list.append(i)
#                  for k in range(0,len(course_subjects_list)):
#                      if course_subjects_list[k]==my_teacher["subject"]:
#                          subject_status=True
#                  if subject_status:
#                      score=int(request.form.get("score"))
#                      #student.update_one({'student_id':stu_id},{'$set':{'subject.$':{'subject_name':my_teacher["subject"],'score':score}}})
#                      student.update_one({'$and':[{'student_id':stu_id},{'subject.subject_name':my_teacher["subject"]}]},{'$set':{'subject.$.score':int(score)}})
#                      my_student = student.find_one({'student_id':stu_id})
#                      score_list =[]
#                      for i in my_student["subject"]:
#                          score_list.append(int(i["score"]))
#                      total_score=0
#                      grade=""
#                      for j in range(0,len(score_list)):
#                          total_score=total_score+int(score_list[j])
#                      total_score=total_score/5
#                      if total_score>=85:
#                          grade="A"
#                      elif total_score<85 and total_score>=75:
#                          grade="B"
#                      elif total_score<75 and total_score>=60:
#                          grade="C"
#                      elif total_score<60 and total_score>=55:
#                          grade="Make Up Exam"
#                      else:
#                          grade="F"
#                      student.update_one({'student_id':stu_id},{'$set':{'average_score':total_score,'grade':grade}})
#                      return "Update Sucessful"
#                  else:
#                      return "Subject is not exist"
#               else:
#                   return "Course is not exist"
#           else:
#               return "Error"
#        else:
#            return "No Authority"
# @app.route("/view_student_detail",methods=['GET'])
# def view_student_detail():
#     header_token = request.headers.get("Authorization")
#     if header_token==None or str(session)=="<SecureCookieSession {}>":
#         return "Please log in first"
#     else:
#        if session['logged_in'] and header_token.split(" ")[1]==session['token'] :
#             student_detail=[]
#             my_students = student.find()
#             for my_student in my_students:
#                 subject_data_list=[]
#                 for j in my_student["subject"]:
#                     subject_data={
#                       "subject_name":j["subject_name"],
#                       "score":j["score"]
#                     }
#                     subject_data_list.append(subject_data)
#                 data = {
#                   "student_name":my_student["name"],
#                   "student_id":my_student["student_id"],
#                   "course_name":my_student["course_name"],
#                   "subject":subject_data_list,
#                   "total_score":my_student["average_score"],
#                   "final grade":my_student["grade"]
#                 }
#                 student_detail.append(data)
#             return student_detail  
#        else:
#             return "No authority"      
# @app.route("/register_csv",methods=['POST'])
# def register_csv():
#     file = request.files["file_name"]
#     filename = secure_filename(file.filename)
#     data = pandas.read_csv(filename)
#     student_id_list=list(data["student_id"].tolist())
#     student_email_list=list(data["student_email"].tolist())
#     student_name_list=list(data["student_name"].tolist())
#     course_id_list=list(data["course_id"].tolist())
#     password_list=list(data["password"].tolist())
#     student_data_list=[]
#     for i in range(0,len(list(student_id_list))):
#         student_data = {
#              "email":student_email_list[i],
#              "name":student_name_list[i],
#              "student_id":student_id_list[i],
#              "password":bcrypt.generate_password_hash(password_list[i]).decode('utf-8'),
#              "course_id":course_id_list[i],
#              "course_name":"course_name",
#              "average_score":0,
#              "grade":"",
#              "subject":"N/A"
#           }
#         student_data_list.append(student_data)
#     for j in range(0,len(student_data_list)):
#         my_student= student.find_one({'$or':[{'email': student_data_list[j]["email"]},{'student_id': student_data_list[j]["student_id"]}]})
#         my_course = course.find_one({'course_id':course_id_list[j]})
#         if my_student==None and my_course!=None :
#            subject=[]
#            for k in range(0,len(my_course["subject"])):
#              subject.append({"subject_name":my_course["subject"][k],"score":0})
#            student_data_list[j]["subject"]=subject
#            student_data_list[j]["course_name"]=my_course["course_name"]
#            student.insert_one(student_data_list[j])
#            return "Success"
with app.app_context():
    db.create_all()

