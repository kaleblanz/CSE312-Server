alphanumeric = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
lower_case = "abcdefghijklmnopqrstuvwxyz"
upper_case = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
single_digit = "0123456789"
special_char = "!@#$%^&()-_="
all_available_char = alphanumeric + special_char

def extract_credentials(request):
    """
    * takes a request object
    * returns a list containing 2 elements, a username then a password, both strings
    test1:
              pb!@#$%^&(()_-=das#@nkn12@31%43212
    password: pb!@#$%^&(()_-=das#@nkn12@31%43212
    password:pb%21%40%23%24%25%5E%26%28%28%29_-%3Ddas%23%40nkn12%4031%2543212
    test2:
             %%5e
    password:%%5e
    password:%25%255e

    print("inside extract_credentials ")
    print(f"request_body: {request.body}")
    print(f"request_path: {request.path}")
    print(f"request_headers: {request.headers}")
    print(f"request_cookies: {request.cookies}")
    """
    url_encoded_str = request.body.decode()
    username,password = url_encoded_str.split("&")
    username = username.split("=")[1]
    password = password.split("=")[1]
    #print(f"username:{username}")
    #print(f"password:{password}")

    password = password.replace("%21","!")
    password = password.replace("%40", "@")
    password = password.replace("%23", "#")
    password = password.replace("%24", "$")
    password = password.replace("%25", "%")
    password = password.replace("%5E", "^")
    password = password.replace("%28", "(")
    password = password.replace("%29", ")")
    password = password.replace("%2D", "-")
    password = password.replace("%5F", "_")
    password = password.replace("%3D", "=")
    password = password.replace("%26", "&")

    #print(f"password:{password}")
    return [username,password]

def validate_password(password):
    """
    * arg -> str -> the password
    * return -> bool -> true if the password meets the 6 criteria, False o/w
    6 criteria:
    * len(password) >= 8
    * password contains a-z
    * password contains A-Z
    * password contains 0-9
    * password contains at least 1 of the 12 special chars
    * does not contain any invalid chars (not alphanumeric or 12 special chars)
    """
    #print("inside validate_password")
    #print(f"given password:{password}")

    #1.) length is larger than 9
    if len(password) < 8:
        return False

    #2.) password contains a-z
    lower_case_bool = False
    for char in password:
        if char in lower_case:
            lower_case_bool = True
    if lower_case_bool == False:
        return False

    #3.) password contains A-Z
    upper_case_bool = False
    for char in password:
        if char in upper_case:
            upper_case_bool = True
    if upper_case_bool == False:
        return False

    #4.)password contains 0-9
    number_bool = False
    for char in password:
        if char in single_digit:
            number_bool = True
    if number_bool == False:
        return False

    #5.) password contains >=1 special char
    special_bool = False
    for char in password:
        if char in special_char:
            special_bool = True
    if special_bool == False:
        return False

    #6.) no invalid chars
    all_chars_valid = True
    for char in password:
        if char not in all_available_char:
            all_chars_valid = False
    if all_chars_valid == False:
        return False

    #all 6 cases passed
    return True


"""
def main():
    assert validate_password("yurr123()12hHSB") == True
    assert validate_password("asFG!@p") == False
    assert validate_password("dJKJLASD&#@&_+") == False
    assert validate_password("dJKJLASD&#@&_*") == False
    assert validate_password("hjOP%^(0") == True
    assert validate_password("pb!@#$%^&(()_-=das#@nkn12@31%43212A") == True


if __name__ == "__main__":
    main()
"""