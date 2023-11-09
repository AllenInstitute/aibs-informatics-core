__all__ = [
    "PrincipalType",
    "UserId",
    "IAMArn",
]
import re
from typing import ClassVar, Optional, Pattern

from aibs_informatics_core.collections import StrEnum, ValidatedStr
from aibs_informatics_core.utils.decorators import cached_property


class PrincipalType(StrEnum):
    Account = "Account"
    User = "User"
    FederatedUser = "FederatedUser"
    AssumedRole = "AssumedRole"
    Anonymous = "Anonymous"


class UserId(ValidatedStr):
    """User ID returned from STS Caller Indentity

    Resources:
    - https://awscli.amazonaws.com/v2/documentation/api/latest/reference/sts/get-caller-identity.html
    - https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html#principaltable
    - https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html#identifiers-unique-ids

    """

    regex_pattern: ClassVar[Pattern] = re.compile(
        r"(?:anonymous|([\d]{12})|([\w\d]{19,21}))(?::(.+))?"
    )

    @property
    def account_id(self) -> Optional[str]:
        return self.get_match_groups()[0]

    @property
    def unique_id(self) -> Optional[str]:
        return self.get_match_groups()[1]

    @property
    def caller_specified_name(self) -> Optional[str]:
        return self.get_match_groups()[2]

    @cached_property
    def principal_type(self) -> PrincipalType:
        if self.account_id and not self.caller_specified_name:
            return PrincipalType.Account
        elif self.unique_id and not self.caller_specified_name:
            return PrincipalType.User
        elif self.account_id and self.caller_specified_name:
            return PrincipalType.FederatedUser
        elif self.unique_id and self.caller_specified_name:
            return PrincipalType.AssumedRole
        else:
            # self == "anonymous"
            return PrincipalType.Anonymous


# https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
class IAMArn(ValidatedStr):
    """

    Possible ARN templates (variables in {}):
        arn:aws:iam::{account}:root
        arn:aws:iam::{account}:user/{user-name-with-path}
        arn:aws:iam::{account}:group/{group-name-with-path}
        arn:aws:iam::{account}:role/{role-name-with-path}
        arn:aws:iam::{account}:policy/{policy-name-with-path}
        arn:aws:iam::{account}:instance-profile/{instance-profile-name-with-path}
        arn:aws:sts::{account}:federated-user/{user-name}
        arn:aws:sts::{account}:assumed-role/{role-name}/{role-session-name}
        arn:aws:iam::{account}:mfa/{virtual-device-name-with-path}
        arn:aws:iam::{account}:u2f/{u2f-token-id}
        arn:aws:iam::{account}:server-certificate/{certificate-name-with-path}
        arn:aws:iam::{account}:saml-provider/{provider-name}
        arn:aws:iam::{account}:oidc-provider/{provider-name}

    Resources:
    - https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
    """

    regex_pattern: ClassVar[Pattern] = re.compile(
        r"""arn:
            aws:
            (iam|sts):
            :                   # usually region, but IAM/STS resources are global
            ([\d]*):            # Account ID

            (
                (
                    root|assumed-role|user|group|role|policy|instance-profile|federated-user|server-certificate|mfa|u2f|.*-provider
                )
                (?:/(.+))?
            )
        """,
        re.X,
    )

    @property
    def account_id(self) -> str:
        return self.get_match_groups()[1]

    @property
    def resource(self) -> str:
        """The resource of the ARN

        Examples:
            - root
            - user/JohnDoe
            - assumed-role/Accounting-Role/JaneDoe
        Returns:
            str: resource
        """
        return self.get_match_groups()[2]

    @property
    def resource_type(self) -> str:
        """The resource Type of the ARN

        Examples are root, user, assumed-role

        Returns:
            str: AWS resource type
        """
        return self.get_match_groups()[3]

    @property
    def resource_id(self) -> str:
        """The resource ID of the ARN

        For most, this follows the first forward slash, but for "root", we return the account id

        Returns:
            str: AWS resource type
        """
        return self.get_match_groups()[4] or self.account_id

    @property
    def resource_name(self) -> str:
        return self.resource_id.split("/")[-1]

    @property
    def resource_path(self) -> str:
        return f"/{'/'.join(self.resource_id.split('/')[:-1])}"
