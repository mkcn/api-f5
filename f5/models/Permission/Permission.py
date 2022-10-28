from f5.models.Permission.Role import Role
from f5.models.Permission.Partition import Partition
from f5.models.Permission.IdentityGroup import IdentityGroup

from f5.models.Permission.repository.Permission import Permission as Repository
from f5.models.Permission.repository.PermissionPrivilege import PermissionPrivilege as PermissionPrivilegeRepository


class Permission:

    # IdentityGroupRolePartition

    def __init__(self, permissionId: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id: int = int(permissionId)
        self.identityGroup: IdentityGroup
        self.role: Role
        self.partition: Partition

        self.__load()



    ####################################################################################################################
    # Public methods
    ####################################################################################################################

    def modify(self, identityGroup: IdentityGroup, role: Role, partition: Partition) -> None:
        try:
            Repository.modify(
                self.id,
                identityGroupId=identityGroup.id,
                roleId=role.id,
                partitionId=partition.id
            )
        except Exception as e:
            raise e



    def delete(self) -> None:
        try:
            Repository.delete(self.id)
        except Exception as e:
            raise e



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def hasUserPermission(groups: list, action: str, assetId: int = 0, partition: str = "") -> bool:
        # Authorizations' list allowed for any (authenticated) user.
        if action == "authorizations_get":
            return True

        # Superadmin's group.
        for gr in groups:
            if gr.lower() == "automation.local":
                return True

        try:
            return bool(
                PermissionPrivilegeRepository.countUserPermissions(groups, action, assetId, partition)
            )
        except Exception as e:
            raise e



    @staticmethod
    def permissionsRawList() -> list:

        #     {
        #         "id": 2,
        #         "identity_group_name": "groupAdmin",
        #         "identity_group_identifier": "cn=groupadmin,cn=users,dc=lab,dc=local",
        #         "role": "admin",
        #         "partition": {
        #             "asset_id": 1,
        #             "name": "any"
        #         }
        #     },

        try:
            return Repository.list()
        except Exception as e:
            raise e



    @staticmethod
    def authorizationsList(groups: list) -> dict:

        #     "assets_get": [
        #         {
        #             "assetId": "1",
        #             "partition": "any"
        #         }
        #     ],
        #     "partitions_get": [
        #         {
        #             "assetId": "1",
        #             "partition": "any"
        #         }
        #     ],
        #     ...

        superadmin = False
        for gr in groups:
            if gr.lower() == "automation.local":
                superadmin = True
                break

        if superadmin:
            # Superadmin's permissions override.
            authorizations = {
                "any": [
                    {
                        "assetId": 0,
                        "partition": "any"
                    }
                ]
            }
        else:
            try:
                authorizations = PermissionPrivilegeRepository.authorizationsList(groups)
            except Exception as e:
                raise e

        return authorizations



    @staticmethod
    def add(identityGroup: IdentityGroup, role: Role, partition: Partition) -> None:
        try:
            Repository.add(
                identityGroupId=identityGroup.id,
                roleId=role.id,
                partitionId=partition.id
            )
        except Exception as e:
            raise e



    ####################################################################################################################
    # Private methods
    ####################################################################################################################

    def __load(self) -> None:
        try:
            info = Repository.get(self.id)

            self.identityGroup = IdentityGroup(id=info["id_group"])
            self.role = Role(id=info["id_role"])
            self.partition = Partition(id=info["id_partition"])
        except Exception as e:
            raise e
