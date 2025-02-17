from django.db import connection

from f5.helpers.Exception import CustomException
from f5.helpers.Database import Database as DBHelper


class Permission:

    # IdentityGroupRolepartition

    # Table: group_role_partition

    #   `id` int(255) NOT NULL AUTO_INCREMENT,
    #   `id_group` int(11) NOT NULL KEY,
    #   `id_role` int(11) NOT NULL KEY,
    #   `id_partition` int(11) NOT NULL KEY
    #
    #   PRIMARY KEY (`id_group`,`id_role`,`id_partition`)
    #
    #   CONSTRAINT `grp_group` FOREIGN KEY (`id_group`) REFERENCES `identity_group` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    #   CONSTRAINT `grp_partition` FOREIGN KEY (`id_partition`) REFERENCES `partition` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    #   CONSTRAINT `grp_role` FOREIGN KEY (`id_role`) REFERENCES `role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def get(permissionId: int) -> dict:
        c = connection.cursor()

        try:
            c.execute("SELECT * FROM group_role_partition WHERE id=%s", [permissionId])

            return DBHelper.asDict(c)[0]
        except IndexError:
            raise CustomException(status=404, payload={"database": "non existent permission"})
        except Exception as e:
            raise CustomException(status=400, payload={"database": e.__str__()})
        finally:
            c.close()



    @staticmethod
    def modify(permissionId: int, identityGroupId: int, roleId: int, partitionId: int) -> None:
        c = connection.cursor()

        try:
            c.execute("UPDATE group_role_partition SET id_group=%s, id_role=%s, id_partition=%s WHERE id=%s", [
                identityGroupId, # AD or RADIUS group.
                roleId,
                partitionId,
                permissionId
            ])
        except Exception as e:
            if e.__class__.__name__ == "IntegrityError" \
                    and e.args and e.args[0] and e.args[0] == 1062:
                raise CustomException(status=400, payload={"database": "duplicated entry"})
            else:
                raise CustomException(status=400, payload={"database": e.__str__()})
        finally:
            c.close()



    @staticmethod
    def delete(permissionId: int) -> None:
        c = connection.cursor()

        try:
            c.execute("DELETE FROM group_role_partition WHERE id = %s", [
                permissionId
            ])
        except Exception as e:
            raise CustomException(status=400, payload={"database": e.__str__()})
        finally:
            c.close()



    @staticmethod
    def list() -> list:
        c = connection.cursor()

        try:
            c.execute(
                "SELECT "
                    "group_role_partition.id, "
                    "identity_group.name AS identity_group_name, "
                    "identity_group.identity_group_identifier AS identity_group_identifier, "
                    "role.role AS role, "
                    "`partition`.id_asset AS partition_asset, "
                    "`partition`.`partition` AS partition_name "
                "FROM identity_group "
                "LEFT JOIN group_role_partition ON group_role_partition.id_group = identity_group.id "
                "LEFT JOIN role ON role.id = group_role_partition.id_role "
                "LEFT JOIN `partition` ON `partition`.id = group_role_partition.id_partition "
                "WHERE role.role IS NOT NULL")
            l = DBHelper.asDict(c)

            for el in l:
                el["partition"] = {
                    "asset_id": el["partition_asset"],
                    "name": el["partition_name"]
                }

                del(el["partition_asset"])
                del(el["partition_name"])

            return l
        except Exception as e:
            raise CustomException(status=400, payload={"database": e.__str__()})
        finally:
            c.close()



    @staticmethod
    def add(identityGroupId: int, roleId: int, partitionId: int) -> None:
        c = connection.cursor()

        try:
            c.execute("INSERT INTO group_role_partition (id_group, id_role, id_partition) VALUES (%s, %s, %s)", [
                identityGroupId, # AD or RADIUS group.
                roleId,
                partitionId
            ])
        except Exception as e:
            if e.__class__.__name__ == "IntegrityError" \
                    and e.args and e.args[0] and e.args[0] == 1062:
                raise CustomException(status=400, payload={"database": "duplicated entry"})
            else:
                raise CustomException(status=400, payload={"database": e.__str__()})
        finally:
            c.close()
