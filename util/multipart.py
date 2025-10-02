from util.MultipartOBJ import MultipartOBJECT
from util.PartOBJ import PartOBJECT


def parse_multipart(request):
    """
    * assume request is a multipart request
    * returns -> an obj containing the fields: boundary and parts
    * boundary -> boundary from Content-Type header
    * parts -> a list of all the parts of the request in the order they appear in the request
    * each Part object must contain:
        headers -> dict of all headers for the part
        name -> name from Content-Disposition header
        content -> content of the part in bytes
    """
    #print(f"request.headers:{request.headers}")
    #print(f"request.body:{request.body}")
    multipart_obj = MultipartOBJECT()
    multipart_obj.boundary = request.headers["Content-Type"].split(";")[1].split("=")[1].strip()
    #print(f"multipart_obj.boundary:{multipart_obj.boundary}")
    part_obj = PartOBJECT()
    part_obj.headers = request.headers
    request_body_split = request.body.split(b"\r\n\r\n",1)[0].decode()
    name = request_body_split.split('\r\n')[1].split("; ")[1].split("=")[1]
    #print(f"name:{name}         type:{type(name)}")
    part_obj.name = name
    part_obj.content = request.body.split(b"\r\n\r\n",1)[1]
    #print(f"part_obj.content:{part_obj.content}")
    multipart_obj.list_of_parts.append(part_obj)

    #print(f"multipart boundary: {multipart_obj.boundary}")
    #print(f"multipart parts: {multipart_obj.list_of_parts[0].name}")
    return multipart_obj
