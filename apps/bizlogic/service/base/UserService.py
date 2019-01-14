# _*_ coding: utf-8 _*_
__author__ = 'seesky@hstecs.com'
__date__ = '2018/12/11 15:01'

from apps.bizlogic.models import Piuser
from apps.bizlogic.models import Piuserrole
from apps.bizlogic.models import Pistaff
from apps.bizlogic.models import Piorganize
from apps.bizlogic.models import Piuserorganize

from django.db.utils import DatabaseError
from django.db.transaction import TransactionManagementError
from django.db import connection
from django.core.paginator import Paginator
from django.db.models import Q

from apps.utilities.publiclibrary.StringHelper import StringHelper
from apps.utilities.message.StatusCode import StatusCode
from apps.utilities.message.FrameworkMessage import FrameworkMessage
from apps.utilities.message.AuditStatus import AuditStatus
from apps.utilities.publiclibrary.DbCommonLibaray import DbCommonLibaray
from apps.utilities.publiclibrary.SystemInfo import SystemInfo
from apps.utilities.message.PermissionScope import PermissionScope

from apps.bizlogic.service.base.OrganizeService import OrganizeService
from apps.bizlogic.service.permission.UserPermission import UserPermission
from apps.bizlogic.service.base.PermissionItemService import PermissionItemService
from apps.bizlogic.service.base.PermissionScopeService import PermissionScopeService

class UserSerivce(object):
    """
    用户服务
    """

    def __init__(self):
        object.__init__()

    def Exists(self, fieldNames, fieldValue):
        """
        用户名是否重复
        Args:
            fieldNames (string): 字段名
            fieldValue (string): 字段值
        Returns:
            returnValue(bool): 已存在
        """
        try:
            Piuser.objects.get(**{fieldNames: fieldValue})
            return True
        except Piuser.DoesNotExist:
            return False

    def AddUser(self, userEntity):
        """
        添加用户
        Args:
            userEntity (Piuser): 用户实体
        Returns:
            returnValue: 用户主键
        """
        try:
            userEntity.save()
            returnCode = StatusCode.statusCodeDic['OKAdd']
            returnMessage = FrameworkMessage.MSG0009
            returnValue = userEntity.id
            return returnCode, returnMessage, returnValue
        except DatabaseError as e:
            print(e)
            returnCode = StatusCode.statusCodeDic['DbError']
            returnMessage = FrameworkMessage.MSG0001
            returnValue = None
            return returnCode, returnMessage, returnValue
        except TransactionManagementError as e:
            print(e)
            returnCode = StatusCode.statusCodeDic['DbError']
            returnMessage = FrameworkMessage.MSG0001
            returnValue = None
            return returnCode, returnMessage, returnValue

    def GetEntity(id):
        """
        获取用户实体
        Args:
            id (string): 用户主键
        Returns:
            returnValue (Piuser or None): 用户实体
        """
        try:
            user = Piuser.objects.get(id=id)
            return user
        except Piuser.DoesNotExist:
            return None


    def GetEntityByUserName(self, userName):
        """
        根据用户名获取用户实体
        Args:
            userName (string): 用户名称
        Returns:
            returnValue (Piuser or None): 用户实体
        """
        try:
            user = Piuser.objects.get(username=userName)
            return user
        except Piuser.DoesNotExist:
            return None


    def GetDT(self):
        """
        获取用户列表
        Args:
        Returns:
            returnValue (List): 用户列表
        """
        returnValue = []
        try:
            for user in Piuser.objects.filter(deletemark=0).order_by('sortcode'):
                returnValue.append(user)
            return returnValue
        except DatabaseError as e:
            return returnValue
        except TransactionManagementError as e:
            return returnValue


    def GetDTByPage(self, searchValue, departmentId, roleId, pageSize=50, order=None):
        """
        分页查询
        Args:
            searchValue (string): 查询字段
            departmentId (string): 部门主键
            roleId (string): 角色主键
            pageSize (int): 每页显示
            order (string): 排序
        Returns:
            returnValue (Paginator): 用户分页列表
        """
        countSqlQuery =' SELECT * FROM ' +  Piuser._meta.db_table + ' WHERE '

        whereConditional = Piuser._meta.db_table + '.DELETEMARK' + ' = 0 ' \
            + " AND " + Piuser._meta.db_table + '.ENABLED' + ' = 1 ' \
            + " AND " + Piuser._meta.db_table + '.ISVISIBLE' + ' = 1 '

        if departmentId:
            organizeIds = OrganizeService.GetChildrensById(self, departmentId)
            if len(organizeIds) != 0:
                whereConditional = whereConditional + " AND (" +  Piuser._meta.db_table + '.COMPANYID IN (' + StringHelper.ArrayToList(self,organizeIds,"\'") + ')' \
                    + " OR " + Piuser._meta.db_table + '.SUBCOMPANYID IN (' + StringHelper.ArrayToList(self,organizeIds,"\'") + ')' \
                    + " OR " + Piuser._meta.db_table + '.DEPARTMENTID IN (' + StringHelper.ArrayToList(self,organizeIds,"\'") + ')' \
                    + " OR " + Piuser._meta.db_table + '.SUBDEPARTMENTID IN (' + StringHelper.ArrayToList(self,organizeIds,"\'") + ')' \
                    + " OR " + Piuser._meta.db_table + '.WORKGROUPID IN (' + StringHelper.ArrayToList(self,organizeIds,"\'") + '))'

        if roleId:
            whereConditional = whereConditional + ' AND ( ' + Piuser._meta.db_table + '.ID IN' \
                + '    (SELECT USERID FROM ' + Piuserrole._meta.db_table \
                + '     WHERE ROLEID = \'' + roleId + '\'' \
                + '     AND ENABLED = 1' \
                + '     AND DELETEMARK = 0 ))'

        if searchValue:
            whereConditional = whereConditional + "  AND (" + searchValue + ')'

        if order:
            whereConditional = whereConditional + " ORDER BY " + order

        countSqlQuery = countSqlQuery + ' ' + whereConditional
        userList = DbCommonLibaray.executeQuery(self, countSqlQuery)
        returnValue = Paginator(userList, pageSize)
        return returnValue

    def GetList(self):
        """
        获取用户列表
        Args:
        Returns:
            returnValue (List): 用户列表
        """
        returnValue = []
        try:
            for user in Piuser.objects.all():
                returnValue.append(user)
            return returnValue
        except DatabaseError as e:
            return returnValue
        except TransactionManagementError as e:
            return returnValue


    def GetDTByIds(self, ids):
        """
         按主键获取用户列表
        Args:
            ids (List[string]): 主键数组
        Returns:
            returnValue (List): 用户列表
        """
        returnValue = []
        for id in ids:
            try:
                user = Piuser.objects.get(id=id)
                returnValue.append(user)
            except Piuser.DoesNotExist:
                continue
        return returnValue

    def GetListByIds(self, ids):
        """
        按主键获取用户列表
        Args:
            ids (List[string]): 主键数组
        Returns:
            returnValue (List): 用户列表
        """
        returnValue = []
        for id in ids:
            try:
                user = Piuser.objects.get(id=id)
                returnValue.append(user)
            except Piuser.DoesNotExist:
                continue
        return returnValue

    def UpdateUser(self, userEntity):
        """
        更新用户
        Args:
            userEntity (Piuser): 用户实体
        Returns:
            returnValue (string): 状态码
            returnMessage (string): 状态信息
        """
        try:
            userEntity.save()
            returnCode = StatusCode.statusCodeDic['OKUpdate']
            returnMessage = FrameworkMessage.MSG0010
            return returnCode,returnMessage
        except:
            returnCode = StatusCode.statusCodeDic['Error']
            returnMessage = FrameworkMessage.MSG0001
            return returnCode, returnMessage

    def GetSearchConditional(self, permissionScopeCode, search, roleIds, enabled, auditStates, departmentId):
        """
        获取SQL查询串
        Args:
            permissionScopeCode (string): 权限码
            search (string): 查询字段
            roleIds     (string[]): 用户角色ID字典
            enabled (string): 启用标志
            auditStates (string): 审核状态
            departmentId (string): 组织机构ID
        Returns:
            returnValue (int): SQL组合查询串
        """
        #easyui search
        whereConditional = 'piuser.DELETEMARK = 0 AND piuser.ISVISIBLE = 1 '
        if enabled:
            whereConditional = whereConditional + ' AND ( piuser.ENABLED = 1 ) '

        if search:
            whereConditional = whereConditional + ' AND ( piuser.USERNAME LIKE \'' + search + '\'' \
                + ' OR piuser.CODE LIKE \'' + search + '\'' \
                + ' OR piuser.REALNAME LIKE \'' + search + '\'' \
                + ' OR piuser.QUICKQUERY LIKE \'' + search + '\'' \
                + ' OR piuser.DEPARTMENTNAME LIKE \'' + search + '\'' \
                + ' OR piuser.DESCRIPTION LIKE \'' + search + '\')'

        if departmentId:
            organizeIds = OrganizeService.GetChildrensById(self, departmentId)
            if len(organizeIds) > 0:
                whereConditional = whereConditional + ' AND (piuser.COMPANYID IN (' + StringHelper.ArrayToList(self, organizeIds, '\'') + ')' \
                    + ' OR piuser.COMPANYID IN (' + StringHelper.ArrayToList(self, organizeIds, '\'') + ')' \
                    + ' OR piuser.DEPARTMENTID IN (' + StringHelper.ArrayToList(self, organizeIds, '\'') + ')' \
                    + ' OR piuser.SUBDEPARTMENTID IN (' + StringHelper.ArrayToList(self, organizeIds, '\'') + ')' \
                    + ' OR piuser.WORKGROUPID IN (' + StringHelper.ArrayToList(self, organizeIds, '\'') + '))'

                whereConditional = whereConditional + ' OR piuser.ID IN (' \
                    + ' SELECT ID' \
                    + ' FROM piuser' \
                    + ' WHERE (piuserorganize.DELETEMARK = 0)' \
                    + ' AND (' \
                    + ' piuserorganize.COMPANYID=' + departmentId + '\' OR ' \
                    + ' piuserorganize.SUBCOMPANYID=' + departmentId + '\' OR ' \
                    + ' piuserorganize.DEPARTMENTID=' + departmentId + '\' OR ' \
                    + ' piuserorganize.SUBDEPARTMENTID=' + departmentId + '\' OR ' \
                    + ' piuserorganize.WORKGROUPID=' + departmentId + '\'))'

        if  auditStates:
            whereConditional = whereConditional + ' AND (piuser.AUDITSTATUS=\'' + auditStates + '\')'

        if roleIds:
            roles = StringHelper.ArrayToList(self, roleIds, '\'')
            whereConditional = whereConditional + ' AND (piuser.ID IN ( SELECT USERID FROM piuserrole WHERE ROLEID IN (' + roles + ')))'

        return whereConditional


    def Searchs(self, permissionScopeCode, search, roleIds, enabled, audiStates, departmentId):
        """
        查询用户
        Args:
            permissionScopeCode (string): 权限码
            search (string): 查询字段
            roleIds     (string[]): 用户角色
            enabled (string): 启用标志
            auditStates (string): 审核状态
            departmentId (string): 组织机构ID
        Returns:
            returnValue (List): 用户列表
        """
        userList = []
        sqlQuery = 'select piuser.*,piuserlogon.FIRSTVISIT,piuserlogon.PREVIOUSVISIT,piuserlogon.LASTVISIT,piuserlogon.IPADDRESS,piuserlogon.MACADDRESS,piuserlogon.LOGONCOUNT,piuserlogon.USERONLINE,piuserlogon.CHECKIPADDRESS,piuserlogon.MULTIUSERLOGIN FROM PIUSER LEFT OUTER JOIN PIUSERLOGON ON PIUSER.ID = PIUSERLOGON.ID '
        whereConditional = UserSerivce.GetSearchConditional(self,permissionScopeCode, search, roleIds, enabled, audiStates, departmentId)
        sqlQuery = sqlQuery + " WHERE " + whereConditional
        sqlQuery = sqlQuery + " ORDER BY piuser.SORTCODE"
        userList = DbCommonLibaray.executeQuery(self, sqlQuery)
        return userList

    def Search(self, searchValue, auditStatus, roleIds):
        """
        查询用户
        Args:
            searchValue (string): 查询字段
            auditStatus (string): 审核状态
            roleIds     (string[]): 用户角色ID字典
        Returns:
            returnValue (int): 影响行数
        """
        returnValue = UserSerivce.Searchs(self, '', searchValue, roleIds, None,   auditStatus, '')
        return returnValue



    def SetUserAuditStates(self, ids, auditStates):
        """
        设置用户审核状态
        Args:
            ids (string[]): 主键数组
            auditStates (string): 审核状态
        Returns:
            returnValue (int): 影响行数
        """
        returnValue = Piuser.objects.filter(id__in=ids).update(auditstatus = auditStates)
        if auditStates == AuditStatus.AuditPass:
            returnValue = Piuser.objects.filter(id__in=ids).update(enable=1)
        if auditStates == AuditStatus.AuditReject:
            returnValue = Piuser.objects.filter(id__in=ids).update(enable=0)
        return returnValue

    def Delete(self, id):
        """
        单个删除用户
        Args:
            id (string): 主键
        Returns:
            returnValue (True or False): 删除结果
        """
        try:
            #已删除用户Piuser表中的DELETEMARK设置为1
            try:
                user = Piuser.objects.get(id=id)
            except Piuser.DoesNotExist as e:
                return False
            user.deletemark = 1
            user.save()
            #用户已经被删除的员工的UserId设置为Null
            Pistaff.objects.filter(userid__in=Piuser.objects.filter(deletemark=1)).update(userid=None)
            # 清除用户的操作权限
            UserPermission.ClearUserPermissionByUserId(self, id)
            return True
        except Exception as e:
            return False


    def BatchDelete(self, ids):
        """
        单个删除用户
        Args:
            ids (string[]): 用户主键列表
        Returns:
            returnValue (True or False): 删除结果
        """
        # 已删除用户Piuser表中的DELETEMARK设置为1
        try:
            user = Piuser.objects.filter(id__in=ids)
            if len(user) == 0:
                return False
            user.update(deletemark=1)
        except Exception as e:
            return False
        # 用户已经被删除的员工的UserId设置为Null
        Pistaff.objects.filter(userid__in=Piuser.objects.filter(id__in=ids)).update(userid=None)
        # 清除用户的操作权限
        for id in ids:
            UserPermission.ClearUserPermissionByUserId(self, id)
        return True


    def SetDeleted(self, ids):
        """
        批量打删除标志
        Args:
            ids (string[]): 用户主键列表
        Returns:
            returnValue (True or False): 影响行数
        """
        try:
            user = Piuser.objects.filter(id__in=ids)
            if len(user) == 0:
                return False
            user.update(deletemark=1)
        except Exception as e:
            return False
        # 清除用户的操作权限
        for id in ids:
            UserPermission.ClearUserPermissionByUserId(self, id)
        return True

    def BatchSave(self, dataTable):
        """
        批量保存
        Args:
            dataTable (Piuser[]): 用户列表
        Returns:
            returnValue (True or False): 保存结果
        """
        try:
            for user in dataTable:
                user.save()
            return True
        except:
            return False

    def GetCompanyUser(self, user):
        """
        得到当前用户所在公司的用户列表
        Args:
            user (Piuser): 当前用户
        Returns:
            returnValue (Piuser[]): 用户列表
        """
        returnValue = Piuser.objects.filter(Q(companyname=user.companyname) & Q(deletemark=0) & Q(enabled=1) & Q(isvisible=1)).order_by('sortcode')
        return returnValue

    def GetDepartmentUser(self, user):
        """
        得到当前用户所在部门的用户列表
        Args:
            user (Piuser): 当前用户
        Returns:
            returnValue (Piuser[]): 用户列表
        """
        returnValue = Piuser.objects.filter(
            Q(companyname=user.companyname) & Q(deletemark=0) & Q(departmentname=user.departmentname) & Q(enabled=1) & Q(isvisible=1)).order_by('sortcode')
        return returnValue

    def GetDTByOrganizes(self, organizeIds):

        organizeList = StringHelper.ArrayToList(self, organizeIds,'\'')

        sqlQuery = " SELECT * " \
            + " FROM " + Piuser._meta.db_table \
            + " WHERE (" + Piuser._meta.db_table + ".deletemark = 0 ) " \
            + "       AND (" + Piuser._meta.db_table + ".workgroupid IN ( " + organizeList + ") " \
            + "       OR " + Piuser._meta.db_table + ".departmentid IN (" + organizeList + ") " \
            + "       OR " + Piuser._meta.db_table + ".companyid IN (" + organizeList + ")) " \
            + " OR id IN (" \
            + " SELECT userid" \
            + "   FROM " + Piuserorganize._meta.db_table \
            + "  WHERE (" + Piuserorganize._meta.db_table + ".deletemark = 0 ) " \
            + "       AND (" + Piuserorganize._meta.db_table + ".workgroupid IN ( " + organizeList + ") " \
            + "       OR " + Piuserorganize._meta.db_table + ".departmentid IN (" + organizeList + ") " \
            + "       OR " + Piuserorganize._meta.db_table + ".companyid IN (" + organizeList + "))) " \
            + " ORDER BY " + Piuser._meta.db_table + ".sortcode";

        return DbCommonLibaray.executeQuery(self, sqlQuery)

    def GetDataTableByDepartment(self, departmentId):
        """
        得到指定组织包含的用户列表
        Args:
            departmentId (string): 组织机构主键
            containChildren (string): 是否包含子部门
        Returns:
            returnValue (List[Dic[Piuser]]): 用户列表
        """
        sqlQuery = " SELECT " + Piuser._meta.db_table + ".*  FROM " + Piuser._meta.db_table \
        + " WHERE (" + Piuser._meta.db_table + ".deletemark = 0 " \
        + " AND " + Piuser._meta.db_table + ".enabled = 1 ) "

        if departmentId:
            sqlQuery = sqlQuery + " AND ((" + Piuser._meta.db_table + ".departmentid = '" + departmentId + "') "
            sqlQuery =  sqlQuery + " OR id IN (" \
            + " SELECT userid" \
            + "   FROM " +Piuserorganize._meta.db_table \
            + "  WHERE (" + Piuserorganize._meta.db_table + ".deletemark = 0 ) " \
            + "       AND (" + Piuserorganize._meta.db_table + ".departmentid = '" + departmentId + "'))) "; \

        returnValue = DbCommonLibaray.executeQuery(self, sqlQuery)
        return returnValue


    def GetDepartmentUsers(self, departmentId, containChildren):
        """
        得到指定部门包含的用户列表
        Args:
            departmentId (string): 部门主键
            containChildren (string): 是否包含子部门
        Returns:
            returnValue (List[Dic[Piuser]]): 用户列表
        """
        returnValue = []
        if not departmentId:
            returnValue = Piuser.objects.filter(Q(deletemark=0)).order_by('sortcode')
        elif containChildren:

            organizeIds = OrganizeService.GetChildrensIdByCode(self, Piorganize.objects.get(id = departmentId).code)
            returnValue = UserSerivce.GetDTByOrganizes(self, organizeIds)
        else:
            returnValue = UserSerivce.GetDataTableByDepartment(self, departmentId)

        return returnValue


    def GetListByDepartment(self, departmentId, containChildren):
        """
        得到指定组织包含的用户列表
        Args:
            departmentId (string): 组织机构主键
            containChildren (string): 是否包含子部门
        Returns:
            returnValue (List[Dic[Piuser]]): 用户列表
        """
        sqlQuery = " SELECT " + Piuser._meta.db_table + ".*  FROM " + Piuser._meta.db_table \
                   + " WHERE (" + Piuser._meta.db_table + ".deletemark = 0 " \
                   + " AND " + Piuser._meta.db_table + ".enabled = 1 ) "

        if departmentId:
            sqlQuery = sqlQuery + " AND ((" + Piuser._meta.db_table + ".departmentid = '" + departmentId + "') "
            sqlQuery = sqlQuery + " OR id IN (" \
                       + " SELECT userid" \
                       + "   FROM " + Piuserorganize._meta.db_table \
                       + "  WHERE (" + Piuserorganize._meta.db_table + ".deletemark = 0 ) " \
                       + "       AND (" + Piuserorganize._meta.db_table + ".departmentid = '" + departmentId + "'))) "; \
        returnValue = DbCommonLibaray.executeQuery(self, sqlQuery)
        return returnValue

    def GetSearchConditional(self, userInfo, permissionScopeCode, search, roleIds, enabled, auditStates, departmentId):
        search = StringHelper.GetSearchString(self, search)
        whereConditional = 'piuser.deletemark=0 and piuser.isvisible=1 '
        if not enabled == None:
            if enabled == True:
                whereConditional = whereConditional + " and ( piuser.enabled = 1 )"
            else:
                whereConditional = whereConditional + " and ( piuser.enabled = 0 )"
        if search:
            whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'username' + " LIKE '" + search + "'" \
                            + " OR " + 'piuser' + "." + 'code' + " LIKE '" + search + "'" \
                            + " OR " + 'piuser' + "." + 'realname' + " LIKE '" + search + "'" \
                            + " OR " + 'piuser' + "." + 'quickquery' + " LIKE '" + search + "'" \
                            + " OR " + 'piuser' + "." + 'departmentname' + " LIKE '" + search + "'" \
                            + " OR " + 'piuser' + "." + 'description' + " LIKE '" + search + "')"
        if departmentId:
            organizeIds = OrganizeService.GetChildrensById(self, departmentId)
            if organizeIds and len(organizeIds) > 0:
                whereConditional =  whereConditional + " AND (" + 'piuser' + "." + 'companyid' + " IN (" + StringHelper.ArrayToList(self, organizeIds,"'") + ")" \
                     + " OR " + 'piuser' + "." + 'companyid' + " IN (" + StringHelper.ArrayToList(self, organizeIds, "'") + ")"   \
                     + " OR " + 'piuser' + "." + 'departmentid' + " IN (" + StringHelper.ArrayToList(self, organizeIds, "'") + ")"    \
                     + " OR " + 'piuser' + "." + 'subdepartmentid' + " IN (" + StringHelper.ArrayToList(self, organizeIds, "'") + ")" \
                     + " OR " + 'piuser' + "." + 'workgroupid' + " IN (" + StringHelper.ArrayToList(self, organizeIds, "'") + "))"
                whereConditional = whereConditional + " OR " + 'piuser' + "." + 'id' + " IN (" \
                            + " SELECT " + 'userid' \
                            + "   FROM " + 'piuserorganize' \
                            + "  WHERE (" + 'piuserorganize' + "." + 'deletemark' + " = 0 ) " \
                            + "       AND ("  \
                            + 'piuserorganize' + "." + 'companyid' + " = '" + departmentId + "' OR " \
                            + 'piuserorganize' + "." + 'subcompanyid' + " = '" + departmentId + "' OR " \
                            + 'piuserorganize' + "." + 'departmentid' + " = '" + departmentId + "' OR " \
                            + 'piuserorganize' + "." + 'subdepartmentid' + " = '" + departmentId + "' OR " \
                            + 'piuserorganize' + "." + 'workgroupid' + " = '" + departmentId + "')) ";
        if auditStates:
            whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'auditstatus' + " = '" + auditStates + "')"

        if roleIds and len(roleIds) > 0:
            roles = StringHelper.ArrayToList(self, roleIds, "'")
            whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'id' + " IN (" + "SELECT " + 'userid' + " FROM " + 'piuserrole' + " WHERE " + 'roleid' + " IN (" + roles + ")" + "))"

        if (not userInfo.IsAdministrator) and SystemInfo.EnableUserAuthorizationScope:
            permissionScopeItemId = PermissionItemService.GetId(self, permissionScopeCode)
            if permissionScopeItemId:
                #从小到大的顺序进行显示，防止错误发生
                organizeIds = PermissionScopeService.GetOrganizeIds(self, userInfo.Id, permissionScopeCode)
                #没有任何数据权限
                if PermissionScope.PermissionScopeDic.get('No') in organizeIds:
                    whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'id' + " = NULL ) "
                #按详细设定的数据
                if PermissionScope.PermissionScopeDic.get('Detail') in organizeIds:
                    userIds = PermissionScopeService.GetUserIds(self, userInfo.Id, permissionScopeCode)
                    whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'id' + " IN (" + StringHelper.ObjectsToList(userIds) + ")) "
                #自己的数据，仅本人
                if PermissionScope.PermissionScopeDic.get('User') in organizeIds:
                    whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'id' + " = '" + userInfo.Id + "') "
                #用户所在工作组数据
                if PermissionScope.PermissionScopeDic.get('UserWorkgroup') in organizeIds:
                    whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'workgroupid' + " = '" + userInfo.WorkgroupId + "') "
                #用户所在部门数据
                if PermissionScope.PermissionScopeDic.get('UserDepartment') in organizeIds:
                    whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'departmentid' + " = '" + userInfo.DepartmentId + "') "
                #用户所在公司数据
                if PermissionScope.PermissionScopeDic.get('UserCompany') in organizeIds:
                    whereConditional = whereConditional + " AND (" + 'piuser' + "." + 'companyid' + " = '" + userInfo.CompanyId + "') "
                #全部数据，这里就不用设置过滤条件了
                if PermissionScope.PermissionScopeDic.get('All') in organizeIds:
                    pass
        return whereConditional


    def GetUserIdsInRole(self, roleId):
        """
        获取员工的角色主键数组
        Args:
            roleId (string): 角色主键
        Returns:
            returnValue (List): 主键数组
        """
        q1 = Piuser.objects.filter(Q(roleid=roleId) & Q(deletemark=0) & Q(enabled=1)).values_list('id', flat=True)
        q2 = Piuserrole.objects.filter(Q(roleid=roleId) & Q(userid__in=Piuser.objects.filter(deletemark=0).values_list('id')) & Q(deletemark=0)).values_list('userid', flat=True)
        returnValue = q1.union(q2)
        return returnValue

    def SearchByPage(self, userInfo, permissionScopeCode, search, roleIds, enabled, auditStates, departmentId, pageIndex = 0, pageSize = 20, order = None):
        whereConditional = UserSerivce.GetSearchConditional(self, userInfo, permissionScopeCode, search, roleIds, enabled, auditStates, departmentId)
        #countSqlQuery = ' SELECT * FROM ' + Piuser._meta.db_table + ' WHERE '
        countSqlQuery = 'SELECT * FROM (SELECT PIUSER.*, PIUSERLOGON.FIRSTVISIT, PIUSERLOGON.PREVIOUSVISIT, PIUSERLOGON.LASTVISIT, PIUSERLOGON.IPADDRESS, PIUSERLOGON.MACADDRESS, PIUSERLOGON.LOGONCOUNT, PIUSERLOGON.USERONLINE, PIUSERLOGON.CHECKIPADDRESS, PIUSERLOGON.MULTIUSERLOGIN FROM PIUSER LEFT OUTER JOIN PIUSERLOGON ON PIUSER.ID = PIUSERLOGON.ID WHERE PIUSER.DELETEMARK = 0  AND PIUSER.ISVISIBLE = 1 AND (PIUSER.ENABLED = 1) ORDER BY PIUSER.SORTCODE) PIUSER WHERE '
        countSqlQuery = countSqlQuery + ' ' + whereConditional
        userList = DbCommonLibaray.executeQuery(self, countSqlQuery)
        pageValue = Paginator(userList, pageSize)
        page = pageValue.page(pageIndex)
        return pageValue.count, page
