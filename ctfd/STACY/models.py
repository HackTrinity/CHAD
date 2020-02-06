from __future__ import division  # Use floating point for math calculations
import math

from flask import Blueprint

from CTFd.models import (
    db,
    Solves,
    Fails,
    Flags,
    Challenges,
    ChallengeFiles,
    Tags,
    Hints,
)
from CTFd.utils.config import is_teams_mode
from CTFd.utils.user import get_ip, get_current_user, is_admin
from CTFd.utils.uploads import delete_file
from CTFd.utils.modes import get_model

from CTFd.plugins.challenges import BaseChallenge
from CTFd.plugins.flags import get_flag_class

class GeneratedFlags(db.Model):
    __tablename__ = "generated_flags"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"))
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"))
    value = db.Column(db.Text)

    @staticmethod
    def is_generated(challenge):
        if challenge.flag_mode > 0 or challenge.flag_mode == -2:
            return True
        if challenge.flag_mode < -2:
            raise ValueError(f"Invalid flag mode {challenge.flag_mode}")
        return False

    @classmethod
    def get_instance_arg(cls, user, challenge):
        if challenge.flag_mode == 0:
            # not mounted or generated
            return False, False
        if challenge.flag_mode == -1:
            # mount static
            flag = Flags.query.filter_by(challenge_id=challenge.id, type="static").first()
            if not flag:
                raise KeyError("no static flags available")
            return flag.content, False

        existing = cls.get(user, challenge)
        if existing:
            # mount existing generated
            return existing.value, False
        if challenge.flag_mode > 0:
            # fixed length generated
            return challenge.flag_mode, True
        if challenge.flag_mode == -2:
            # random length generated
            return True, True

        raise ValueError(f"Invalid flag mode {challenge.flag_mode}")

    @classmethod
    def create(cls, user, challenge, value):
        args = dict(challenge_id=challenge.id, value=value)
        if is_teams_mode() and not is_admin():
            args["team_id"] = user.team_id
        else:
            args["user_id"] = user.id

        flag = cls(**args)
        db.session.add(flag)
        db.session.commit()
        db.session.close()
        return flag

    @classmethod
    def get(cls, user, challenge):
        if is_teams_mode() and not is_admin():
            return cls.query.filter_by(team_id=user.team_id, challenge_id=challenge.id).first()
        else:
            return cls.query.filter_by(user_id=user.id, challenge_id=challenge.id).first()

    @classmethod
    def clear(cls, challenge):
        cls.query.filter_by(challenge_id=challenge.id).delete()
        db.session.commit()
        db.session.close()

    def as_static(self):
        return Flags(content=self.value)

class CHADChallengeModel(Challenges):
    __tablename__ = "chad_challenges"
    __mapper_args__ = {"polymorphic_identity": "chad"}
    id = db.Column(None, db.ForeignKey("challenges.id"), primary_key=True)
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)
    stack = db.Column(db.Text)
    service = db.Column(db.String(80))
    flag_mode = db.Column(db.Integer, default=0)

    @staticmethod
    def parse_flag_mode(data):
        random_length = int(data.pop('random_flag_length', 40))
        if 'flag_mode' in data:
            flag_mode = int(data['flag_mode'])
            if flag_mode > 0:
                data['flag_mode'] = random_length

    def __init__(self, *args, **kwargs):
        CHADChallengeModel.parse_flag_mode(kwargs)
        super(CHADChallengeModel, self).__init__(**kwargs)
        self.initial = kwargs["value"]

class CHADChallenge(BaseChallenge):
    id = "chad"  # Unique identifier used to register challenges
    name = "CHAD"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/STACY/assets/create.html",
        "update": "/plugins/STACY/assets/update.html",
        "view": "/plugins/STACY/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/STACY/assets/create.js",
        "update": "/plugins/STACY/assets/update.js",
        "view": "/plugins/STACY/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/STACY/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "chad",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )

    @classmethod
    def calculate_value(cls, challenge):
        Model = get_model()

        solve_count = (
            Solves.query.join(Model, Solves.account_id == Model.id)
            .filter(
                Solves.challenge_id == challenge.id,
                Model.hidden == False,
                Model.banned == False,
            )
            .count()
        )

        # If the solve count is 0 we shouldn't manipulate the solve count to
        # let the math update back to normal
        if solve_count != 0:
            # We subtract -1 to allow the first solver to get max point value
            solve_count -= 1

        # It is important that this calculation takes into account floats.
        # Hence this file uses from __future__ import division
        value = (
            ((challenge.minimum - challenge.initial) / (challenge.decay ** 2))
            * (solve_count ** 2)
        ) + challenge.initial

        value = math.ceil(value)

        if value < challenge.minimum:
            value = challenge.minimum

        challenge.value = value
        db.session.commit()
        return challenge

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
        challenge = CHADChallengeModel(**data)

        db.session.add(challenge)
        db.session.commit()

        return challenge

    @staticmethod
    def read(challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = CHADChallengeModel.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": CHADChallenge.id,
                "name": CHADChallenge.name,
                "templates": CHADChallenge.templates,
                "scripts": CHADChallenge.scripts,
            },
        }
        return data

    @staticmethod
    def update(challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()
        CHADChallengeModel.parse_flag_mode(data)
        for attr, value in data.items():
            # We need to set these to floats so that the next operations don't operate on strings
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        return CHADChallenge.calculate_value(challenge)

    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.

        :param challenge:
        :return:
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        CHADChallengeModel.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()

    @staticmethod
    def attempt(challenge, request):
        """
        This method is used to check whether a given input is right or wrong. It does not make any changes and should
        return a boolean for correctness and a string to be shown to the user. It is also in charge of parsing the
        user's input from the request itself.

        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return: (boolean, string)
        """
        user = get_current_user()

        data = request.form or request.get_json()
        submission = data["submission"].strip()
        flags = Flags.query.filter_by(challenge_id=challenge.id).all()
        for flag in flags:
            if get_flag_class(flag.type).compare(flag, submission):
                return True, "Correct"

        generated_flag = GeneratedFlags.get(user, challenge)
        if generated_flag and get_flag_class('static').compare(generated_flag.as_static(), submission):
            return True, "Correct"

        return False, "Incorrect"

    @staticmethod
    def solve(user, team, challenge, request):
        """
        This method is used to insert Solves into the database in order to mark a challenge as solved.

        :param team: The Team object from the database
        :param chal: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        challenge = CHADChallengeModel.query.filter_by(id=challenge.id).first()
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        solve = Solves(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(req=request),
            provided=submission,
        )
        db.session.add(solve)
        db.session.commit()

        CHADChallenge.calculate_value(challenge)

    @staticmethod
    def fail(user, team, challenge, request):
        """
        This method is used to insert Fails into the database in order to mark an answer incorrect.

        :param team: The Team object from the database
        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        wrong = Fails(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(request),
            provided=submission,
        )
        db.session.add(wrong)
        db.session.commit()
        db.session.close()
