from flaskAssignment import db,app
from flask_migrate import Migrate
import datetime
from sqlalchemy.orm import backref,Mapped,relationship
import bcrypt
post_tag = db.Table('post_tag',
                    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                    )
class User(db.Model):
    __tablename__='_user'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    email = db.Column(db.String(150),unique=True,nullable=False)
    name = db.Column(db.String(85),nullable=False)
    user_id = db.Column(db.String(100),nullable=False,unique=True)
    password=db.Column(db.String(400),nullable=False)
    _is_login_=db.Column(db.Boolean,default=False,nullable=True)
    department_id=db.Column(db.Integer,db.ForeignKey('department.id'),nullable=False)
    role_id = db.Column(db.Integer,db.ForeignKey('role.id'),nullable=False)
    role=db.relationship('Role', backref='user', lazy=True)
    department =db.relationship('Department', backref='user', lazy=True)
    post = db.relationship('Post',backref='user',lazy=True)
    profile =db.relationship('Profile',backref='user',uselist=False)
    teachersubject=db.relationship("TeacherSubject",backref="user",lazy=True)
    #profile: Mapped['Profile'] = relationship(back_populates="user")
class Role(db.Model):
      __tablename__='role'
      id=db.Column(db.Integer,primary_key=True)
      role_name = db.Column(db.String(60),nullable=False,unique=True)
class Department(db.Model):
      __tablename__='department'
      id=db.Column(db.Integer,primary_key=True)
      department_name=db.Column(db.String(100),unique=True,nullable=False)
      subject = db.relationship("Subject",backref='department',lazy=True)
class Subject(db.Model):
      __tablename__='subject'
      id =db.Column(db.Integer,primary_key=True,unique=True)
      subject_name = db.Column(db.String,nullable=False,unique=True)
      department_id = db.Column(db.Integer,db.ForeignKey('department.id'))
      post=db.relationship("Post",backref='subject',lazy=True)
      teachersubject=db.relationship("TeacherSubject",backref="subject",lazy=True)
class Post(db.Model):
      __tablename__='post'
      id=db.Column(db.Integer,primary_key=True)
      posted_by=db.Column(db.Integer,db.ForeignKey(User.id),nullable=False)
      assignment_titile = db.Column(db.String(190),nullable=False)
      assignment_content=db.Column(db.String(1000),nullable=False,)
      subject_id=db.Column(db.Integer,db.ForeignKey('subject.id'),nullable=False)
      maximium_score=db.Column(db.Integer,default=100)
      remark=db.Column(db.String(190),nullable=False,unique=False)
      date_posted =db.Column(db.DateTime,nullable=False,default=datetime.datetime.utcnow())
      deadline =db.Column(db.DateTime,nullable=False)
      tags=db.relationship("Tag",secondary=post_tag,backref='posts')
class Profile(db.Model):
      __tablename__='profile'
      profile_id=db.Column(db.Integer,primary_key=True)
      user_id=db.Column(db.Integer,db.ForeignKey("_user.id"),nullable=False,unique=True)
      user_name=db.Column(db.String(85),nullable=False)
      email = db.Column(db.String(100),nullable=False,unique=True)
      department=db.Column(db.String(100),nullable=False)
      nationality=db.Column(db.String(100),default="Cambodian")
      dateofbirth=db.Column(db.DateTime,nullable=True)
      phonenumber=db.Column(db.String(15),nullable=True)
class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)
class TeacherSubject(db.Model):
    __tablename__='teachersubject'
    id = db.Column(db.Integer,primary_key=True)
    teacher_id = db.Column(db.Integer,db.ForeignKey("_user.id"),unique=True)
    subject_id=db.Column(db.Integer,db.ForeignKey("subject.id"),unique=True)
    department_id=db.Column(db.Integer,db.ForeignKey("department.id"))
class Tag(db.Model):
     __tablename__='tag'
     id=db.Column(db.Integer,primary_key=True)
     name=db.Column(db.String(100),nullable=False)

    # many-to-one scalar
#1.Student Collection
# student=db["Student"]
# teacher=db["Teacher"]
# course=db["Course"]
# post=db["Post"]