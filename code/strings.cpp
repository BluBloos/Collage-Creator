// TODO(Noah): Would string interning speed up my program? If I only did one pass over all the text, then no. Otherwise, probrably. By how much. Probably a substantial amount.

unsigned int StrLen(char *str)
{
    unsigned int count = 0;
	while (*str != 0)
	{
		str++; count++;
	}
	return count;
}

void StrCpy(char *dest, unsigned int destLen, char *src, unsigned int srcLen)
{
	unsigned int count = 0;
	
	while (*src != 0 && count < srcLen && count < destLen)
	{
		*dest++ = *src++;
		count += 1;
	}
	
	if (count < destLen)
	{
		*dest = 0;
	}
}

// NOTE(Noah): This function does no checking what so over. It assumes that it's passed valid lengths such that it will never access memory it shouldn't!
bool StrEquals(char *str1, char *str2, unsigned int length1, unsigned int length2)
{
    if (length1 != length2)
    {
        return false;
    }
    
    for (unsigned int x = 0; x < length1; x++)
    {
        if (*str1++ == *str2++)
        {
            continue;
        }
        return false;
    }
    
    return true;
}

bool IsDigit(char character)
{
    switch(character)
    {
        case '0':
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
        case '9':
        return true;
        default:
        return false;
    }
}
bool IsLetter(char character)
{
    switch(character)
    {
        case 'a':
        case 'b':
        case 'c':
        case 'd':
        case 'e':
        case 'f':
        case 'g':
        case 'h':
        case 'i':
        case 'j':
        case 'k':
        case 'l':
        case 'm':
        case 'n':
        case 'o':
        case 'p':
        case 'q':
        case 'r':
        case 's':
        case 't':
        case 'u':
        case 'v':
        case 'w':
        case 'x':
        case 'y':
        case 'z':
        case 'A':
        case 'B':
        case 'C':
        case 'D':
        case 'E':
        case 'F':
        case 'G':
        case 'H':
        case 'I':
        case 'J':
        case 'K':
        case 'L':
        case 'M':
        case 'N':
        case 'O':
        case 'P':
        case 'Q':
        case 'R':
        case 'S':
        case 'T':
        case 'U':
        case 'V':
        case 'W':
        case 'X':
        case 'Y':
        case 'Z':
        return true;
        default:
        return false;
    }
}

// TODO(Noah): Do some rigorous testing on the functions below!

// NOTE(Noah): Your boy expects that strOut is a clean input
void IntToASCII(long long number, char *strOut)
{
    unsigned int i = 0;
    bool negative = false;
    if (number < 0)
    {
        
        // with 2's compliment there is 1 more negative than pistive numbers. What happens when I negate the lowest negative?
        number = -number;
        negative = true;
    }
    
    if (number == 0)
    {
        strOut[i++] = '0';
    }
    
    while(number)
    {
        char character = number % 10 + '0';
        number = number / 10;
        strOut[i++] = character;
    }
    
    if (negative)
    {
        strOut[i++] = '-';
    }
    
    // NOTE(Noah): Keep i at the length!
    
    for (unsigned int x = 0; x < i / 2; x++)
    {
        char valA = strOut[x];
        char valB = strOut[i-1-x];
        
        strOut[x] = valB;
        strOut[i-1-x] = valA;
    }
}

void UIntToASCII(long long number, char *strOut)
{
    unsigned int i = 0;
    
    if (number == 0)
    {
        strOut[i++] = '0';
    }
    
    while(number)
    {
        char character = number % 10 + '0';
        number = number / 10;
        strOut[i++] = character;
    }
    
    // NOTE(Noah): Keep i at the length!
    
    for (unsigned int x = 0; x < i / 2; x++)
    {
        char valA = strOut[x];
        char valB = strOut[i-1-x];
        
        strOut[x] = valB;
        strOut[i-1-x] = valA;
    }
}