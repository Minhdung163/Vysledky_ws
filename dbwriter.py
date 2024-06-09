import json
import datetime
from uuid import uuid4
from functools import cache, lru_cache
from async_lru import alru_cache
import asyncio
from pathlib import Path
 
import getpass
import aiohttp
import requests
 
class DBWriter:
    def __init__(self, username="john.newbie@world.com", password="john.newbie@world.com"):
        self.username = username
        self.password = password
        self.token = None
        pass
 
    async def getToken(self):
        # keyurl = "http://host.docker.internal:33001/oauth/login3"
        if self.token:
            return self.token
       
        keyurl = "http://localhost:33001/oauth/login3"
        async with aiohttp.ClientSession() as session:
            async with session.get(keyurl) as resp:
                # print(resp.status)
                keyJson = await resp.json()
                # print(keyJson)
 
            payload = {"key": keyJson["key"], "username": self.username, "password": self.password}
            async with session.post(keyurl, json=payload) as resp:
                # print(resp.status)
                tokenJson = await resp.json()
                # print(tokenJson)
        self.token = tokenJson.get("token", None)
        return self.token
 
    async def queryGQL(self, query, variables):
        # gqlurl = "http://host.docker.internal:33001/api/gql"
        gqlurl = "http://localhost:33001/api/gql"
        token = self.token
        if token is None:
            token = await self.getToken()
        payload = {"query": query, "variables": variables}
        # headers = {"Authorization": f"Bearer {token}"}
        cookies = {'authorization': token}
        async with aiohttp.ClientSession() as session:
            # print(headers, cookies)
            async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
                # print(resp.status)
                if resp.status != 200:
                    text = await resp.text()
                    print(f"failed query \n{query}\n with variables {variables}".replace("'", '"'))
                    print(f"failed resp.status={resp.status}, text={text}")
                    raise Exception(f"Unexpected GQL response", text)
                else:
                    response = await resp.json()
                    return response  
               
    async def queryGQL3(self, query, variables):
        times = 3
        result = None
        for i in range(times):
            try:
                result = await self.queryGQL(query=query, variables=variables)
                if result.get("errors", None) is None:
                    return result
                print(result)
            except Exception:
                pass
 
            await asyncio.sleep(10)
               
        raise Exception(f"unable to run query={query} with variables {variables} for {times} times\n{result}".replace("'", '"'))
 
    @cache
    def GetQuery(self, tableName, queryType):
        assert queryType in ["read", "readp", "create", "update"], f"unknown queryType {queryType}"
        queryfile = f"./gqls/{tableName}/{queryType}.gql"
        # querySet = self.GetQuerySet(tableName=tableName)
        # query = querySet.get(queryType, None)
        with open(queryfile, "r", encoding="utf-8") as fi:
            lines = fi.readlines()
        query = ''.join(lines)
        assert query is not None, f"missing {queryType} query for table {tableName}"
        return query
 
    @alru_cache(maxsize=1024)
    async def asyncTranslateID(self, outer_id, type_id):
        """prevede vnejsi id na vnitrni id pro dany typ,
        napr id (UCO) na id odpovidajici entity v nasem systemu
        """
       
        query = 'query($type_id: UUID!, $outer_id: String!){ result: internalId(typeidId: $type_id, outerId: $outer_id) }'
        jsonData = await self.queryGQL3(query=query, variables={"outer_id": outer_id, "type_id": type_id})
        data = jsonData.get("data", {"result": None})
        result = data.get("result", None)
        return result
   
    @alru_cache()
    async def getAllTypes(self):
        query = self.GetQuery(tableName="externalidtypes", queryType="readp")
        jsonData = await self.queryGQL3(query=query, variables={"limit": 1000})
        data = jsonData.get("data", {"result": None})
        result = data.get("result", None)
        assert result is not None, f"unable to get externalidtypes"
        asdict = {item["name"]: item["id"] for item in result}
        return asdict
 
    @alru_cache(maxsize=1024)
    async def getTypeId(self, typeName):
        """podle typeName zjisti typeID
           cte pomoci query na gql endpointu
        """
        alltypes = await self.getAllTypes()
        result = alltypes.get(typeName, None)
        assert result is not None, f"unable to get id of type {typeName}"
        return result
 
    async def registerID(self, inner_id, outer_id, type_id):
        # assert inner_id is not None, f"missing {inner_id} in registerID"
        # assert outer_id is not None, f"missing {outer_id} in registerID"
        # assert type_id is not None, f"missing {type_id} in registerID"
 
        "zaregistruje vnitrni hodnotu primarniho klice (inner_id) a zpristupni jej pres puvodni id (outer_id a type_id)"
        mutation = '''
            mutation ($type_id: UUID!, $inner_id: UUID!, $outer_id: String!) {
                result: externalidInsert(
                    externalid: {innerId: $inner_id, typeidId: $type_id, outerId: $outer_id}
                ) {
                    msg
                    result: externalid {
                        id    
                        }
                    }
                }
        '''
        jsonData = await self.queryGQL3(query=mutation, variables={"inner_id": inner_id, "outer_id": outer_id, "type_id": type_id})
        data = jsonData.get("data", {"result": {"msg": "fail"}})
        msg = data["result"]["msg"]
        if msg != "ok":
            print(f'register ID failed ({ {"inner_id": inner_id, "outer_id": outer_id, "type_id": type_id} })\n\tprobably already registered')
        else:
            print(f"registered {outer_id} for {inner_id} ({type_id})")
        return "ok"
 
    async def Read(self, tableName, variables, outer_id=None, outer_id_type_id=None):
        if outer_id:
            # read external id
            assert outer_id_type_id is not None, f"if outer_id ({outer_id}) defined, outer_id_type_id must be defined also "
            inner_id = await self.asyncTranslateID(outer_id=outer_id, type_id=outer_id_type_id)
            assert inner_id is not None, f"outer_id {outer_id} od type_id {outer_id_type_id} mapping failed on table {tableName}"
            variables = {**variables, "id": inner_id}
 
        queryRead = self.GetQuery(tableName, "read")
        response = await self.queryGQL3(query=queryRead, variables=variables)
        error = response.get("errors", None)
        assert error is None, f"error {error} during query \n{queryRead}\n with variables {variables}".replace("'", '"')
        data = response.get("data", None)
        assert data is not None, f"got no data during query \n{queryRead}\n with variables {variables}".replace("'", '"')
        result = data.get("result", None)
        # assert result is not None, f"missint result in response \n{response}\nto query \n{queryRead}\n with variables {variables}".replace("'", '"')
        return result
   
    async def Create(self, tableName, variables, outer_id=None, outer_id_type_id=None):
        queryType = "create"
        if outer_id:
            # read external id
            assert outer_id_type_id is not None, f"if outer_id ({outer_id}) defined, outer_id_type_id must be defined also "
            inner_id = await self.asyncTranslateID(outer_id=outer_id, type_id=outer_id_type_id)
           
            if inner_id:
                print(f"outer_id ({outer_id}) defined ({outer_id_type_id}) \t on table {tableName},\t going update")
                old_data = await self.Read(tableName=tableName, variables={"id": inner_id})
                if old_data is None:
                    print(f"found corrupted data, entity with id {inner_id} in table {tableName} is missing, going to create it")
                    variables = {**variables, "id": inner_id}
                else:
                    variables = {**old_data, **variables, "id": inner_id}
                    queryType = "update"
            else:
                print(f"outer_id ({outer_id}) undefined ({outer_id_type_id}) \t on table {tableName},\t going insert")
                registrationResult = await self.registerID(
                    inner_id=variables["id"],
                    outer_id=outer_id,
                    type_id=outer_id_type_id
                    )
                assert registrationResult == "ok", f"Something is really bad, ID reagistration failed"
 
        query = self.GetQuery(tableName, queryType)
        assert query is not None, f"missing {queryType} query for table {tableName}"
        response = await self.queryGQL3(query=query, variables=variables)
        data = response["data"]
        result = data["result"] # operation result
        result = result["result"] # entity result
        return result