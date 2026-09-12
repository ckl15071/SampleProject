#include "./test/test.h"
#include <stdint.h>

/******************************************************************************/
/* ê‡ñæ                                                                       */
/* ê‡ñæ                                                                       */
/* ê‡ñæ                                                                       */
/* ê‡ñæ                                                                       */
/* ê‡ñæ                                                                       */
/******************************************************************************/
int main( int argc, char **argv )
{
    uint8_t u8t_value1;
    uint8_t u8t_value2;
    uint8_t u8t_result;

    test(   );          // test
    test(  );       /* test call 2*/
    test()   ;      /* test call 3 */

    u8t_result=u8g_add_u8u8_u8(u8t_value1,u8t_value2);      /* test */

    return u8t_result;
}
