from dataclasses import dataclass, field
import datetime

@dataclass
class UserDTO:
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    profile_photo: str = ''

    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "password": self.password,
            "role": self.role,
            "profile_photo": self.profile_photo
        }

@dataclass
class RequestDTO:
    user: str
    requested_role: str
    status: str
    submitted_at: str = field(default_factory=lambda: str(datetime.datetime.utcnow()))