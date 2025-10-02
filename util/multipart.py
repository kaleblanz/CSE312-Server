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
    print(f"request.headers:{request.headers}")
    print(f"request.body:{request.body}")
    multipart_obj = MultipartOBJECT()
    multipart_obj.boundary = request.headers["Content-Type"].split(";")[1].split("=")[1].strip()
    print(f"multipart_obj.boundary:{multipart_obj.boundary}")
    part_obj = PartOBJECT()
    part_obj.headers = request.headers
    #part_obj.name =
