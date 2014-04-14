#
# Copyright (C) 2014 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

class ModelBase(object):
    pass

class ModelUser(ModelBase):
    def __init__(self, name, email=None, username=None):
        self.name = name
        self.email = email
        self.username = username

    def is_in_list(self, users):
        if self.name is not None and self.name in users:
            return True
        if self.username is not None and self.username in users:
            return True
        return False

    @staticmethod
    def from_json(data):
        return ModelUser(data.get("name", None),
                         data.get("email", None),
                         data.get("username", None))


class ModelFile(ModelBase):
    ACTION_MODIFIED = "MODIFIED"
    ACTION_ADDED = "ADDED"
    ACTION_DELETED = "DELETED"
    ACTION_RENAMED = "RENAMED"

    def __init__(self, path, action):
        self.path = path
        self.action = action

    @staticmethod
    def from_json(data):
        return ModelFile(data.get("file", None),
                         data.get("type", None))


class ModelApproval(ModelBase):
    ACTION_VERIFIED = "VRIF"
    ACTION_REVIEWED = "CRVW"
    ACTION_APPROVED = "APRV"
    ACTION_SUBMITTED = "SUBM"

    def __init__(self, action, value, grantedOn=None, user=None):
        self.action = action
        self.value = value
        if grantedOn is not None:
            self.grantedOn = int(grantedOn)
        else:
            self.grantedOn = None
        self.user = user

    def is_user_in_list(self, users):
        if self.user is None:
            return False
        return self.user.is_in_list(users)

    @staticmethod
    def from_json(data):
        user = None
        if data.get("by", None):
            user = ModelUser.from_json(data["by"])
        return ModelApproval(data.get("type", None),
                             data.get("value", None),
                             data.get("grantedOn", None),
                             user)


class ModelPatch(ModelBase):

    def __init__(self, number, revision, ref, uploader, createdOn, approvals=[], files=[], comments=[]):
        self.number = number
        self.revision = revision
        self.ref = ref
        self.uploader = uploader
        self.createdOn = createdOn
        self.approvals = approvals
        self.files = files
        self.comments = comments

    @staticmethod
    def is_user_in_list(users, user):
        if user.username is not None and user.username in users:
            return True

        if user.email is not None and user.email in users:
            return True

        return False

    def has_other_reviewers(self, excludeusers):
        '''Determine if the patch has been reviewed by any
        users that are not in 'excludeusers'''

        hasReviewers = False
        for approval in self.approvals:
            if not approval.is_user_in_list(excludeusers):
                hasReviewers = True
        return hasReviewers

    def has_reviewers(self, includeusers):
        '''Determine if the patch has been reviewed by any
        users that are in 'includeusers'''

        hasReviewers = False
        for approval in self.approvals:
            if approval.user is None:
                continue
            if approval.is_user_in_list(includeusers):
                hasReviewers = True
        return hasReviewers

    @staticmethod
    def from_json(data):
        files = []
        for f in data.get("files", []):
            files.append(ModelFile.from_json(f))

        approvals = []
        for f in data.get("approvals", []):
            approvals.append(ModelApproval.from_json(f))

        user = None
        if "uploader" in data:
            user = ModelUser.from_json(data["uploader"]),

        return ModelPatch(int(data.get("number", 0)),
                          data.get("revision"),
                          data.get("ref"),
                          user,
                          data.get("createdOn"),
                          approvals,
                          files)


class ModelChange(ModelBase):

    def __init__(self, project, branch, topic, id, number, subject, owner, url, createdOn, lastUpdated, status, patches = []):
        self.project = project
        self.branch = branch
        self.topic = topic
        self.id = id
        self.number = number
        self.subject = subject
        self.owner = owner
        self.url = url
        if createdOn is not None:
            self.createdOn = int(createdOn)
        else:
            self.createdOn = None
        if lastUpdated is not None:
            self.lastUpdated = int(lastUpdated)
        else:
            self.lastUpdated = None
        self.status = status
        self.patches = patches

    def get_current_patch(self):
        if len(self.patches) == 0:
            return None
        return self.patches[len(self.patches) - 1]

    @staticmethod
    def is_user_in_list(users, user):
        if user.username is not None and user.username in users:
            return True

        if user.email is not None and user.email in users:
            return True

        return False

    def has_any_other_reviewers(self, excludeusers):
        '''Determine if any patch in the change has been
        reviewed by any user not in the list of 'excludeusers'''

        hasReviewers = False
        for patch in self.patches:
            if patch.has_other_reviewers(excludeusers):
                hasReviewers = True
        return hasReviewers

    def has_any_reviewers(self, includeusers):
        '''Determine if any patch in the change has been
        reviewed by any user in the list of 'includeusers'''

        hasReviewers = False
        for patch in self.patches:
            if patch.has_reviewers(includeusers):
                hasReviewers = True
        return hasReviewers

    def has_current_reviewers(self, includeusers):
        '''Determine if the current patch version has
        been reviewed by any of the users in 'includeusers'. '''
        patch = self.get_current_patch()
        if patch is None:
            return False
        return patch.has_reviewers(includeusers)

    def has_current_other_reviewers(self, excludeusers):
        '''Determine if the current patch version has
        been reviewed by any of the users not in 'excludeusers'. '''
        patch = self.get_current_patch()
        if patch is None:
            return False
        return patch.has_other_reviewers(excludeusers)

    @staticmethod
    def from_json(data):
        patches = []
        for p in data.get("patchSets", []):
            patches.append(ModelPatch.from_json(p))

        user = None
        if "owner" in data:
            user = ModelUser.from_json(data["owner"])

        return ModelChange(data.get("project", None),
                           data.get("branch", None),
                           data.get("topic", None),
                           data.get("id", None),
                           data.get("number", None),
                           data.get("subject", None),
                           user,
                           data.get("url", None),
                           data.get("createdOn", None),
                           data.get("lastUpdated", None),
                           data.get("status", None),
                           patches)


class ModelEvent(ModelBase):

    def __init__(self, change, patch, user):
        self.change = change
        self.patch = patch
        self.user = user

    @staticmethod
    def from_json(data):
        if data["type"] == "comment-added":
            return ModelEventCommentAdd.from_json(data)
        elif data["type"] == "patchset-created":
            return ModelEventPatchCreate.from_json(data)
        elif data["type"] == "change-merged":
            return ModelEventChangeMerge.from_json(data)
        elif data["type"] == "change-abandoned":
            return ModelEventChangeAbandon.from_json(data)
        elif data["type"] == "change-restored":
            return ModelEventChangeRestore.from_json(data)
        elif data["type"] == "ref-updated":
            pass
        else:
            raise Exception("Unknown event '%s'" % data["type"])


class ModelEventCommentAdd(ModelEvent):

    def __init__(self, change, patch, user, comment, approvals):
        ModelEvent.__init__(self, change, patch, user)
        self.comment = comment
        self.approvals = approvals

    @staticmethod
    def from_json(data):
        change = ModelChange.from_json(data["change"])
        patch = ModelPatch.from_json(data["patchSet"])
        user = ModelUser.from_json(data["author"])
        comment = data["comment"]
        approvals = []
        for f in data.get("approvals", []):
            approvals.append(ModelApproval.from_json(f))
        return ModelEventCommentAdd(change, patch, user, comment, approvals)


class ModelEventPatchCreate(ModelEvent):

    def __init__(self, change, patch, user):
        ModelEvent.__init__(self, change, patch, user)

    @staticmethod
    def from_json(data):
        change = ModelChange.from_json(data["change"])
        patch = ModelPatch.from_json(data["patchSet"])
        user = ModelUser.from_json(data["uploader"])
        return ModelEventPatchCreate(change, patch, user)


class ModelEventChangeMerge(ModelEvent):

    def __init__(self, change, patch, user):
        ModelEvent.__init__(self, change, patch, user)

    @staticmethod
    def from_json(data):
        change = ModelChange.from_json(data["change"])
        patch = ModelPatch.from_json(data["patchSet"])
        user = ModelUser.from_json(data["submitter"])
        return ModelEventChangeMerge(change, patch, user)


class ModelEventChangeAbandon(ModelEvent):

    def __init__(self, change, patch, user):
        ModelEvent.__init__(self, change, patch, user)

    @staticmethod
    def from_json(data):
        change = ModelChange.from_json(data["change"])
        patch = ModelPatch.from_json(data["patchSet"])
        user = ModelUser.from_json(data["abandoner"])
        return ModelEventChangeAbandon(change, patch, user)


class ModelEventChangeRestore(ModelEvent):

    def __init__(self, change, patch, user):
        ModelEvent.__init__(self, change, patch, user)

    @staticmethod
    def from_json(data):
        change = ModelChange.from_json(data["change"])
        patch = ModelPatch.from_json(data["patchSet"])
        user = ModelUser.from_json(data["restorer"])
        return ModelEventChangeRestore(change, patch, user)
