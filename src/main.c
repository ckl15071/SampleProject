#include "./test/test.h"
#include <stdint.h>

/******************************************************************************/
/* 説明                                                                       */
/* 説明                                                                       */
/* 説明                                                                       */
/* 説明                                                                       */
/* 説明                                                                       */
/******************************************************************************/
int main( int argc, char **argv )
{
    uint8_t u8t_value1;
    uint8_t u8t_value2;
    uint8_t u8t_result;

    test();
    test();
    test();

    u8t_result = u8g_add_u8u8_u8( u8t_value1, u8t_value2 );

    return u8t_result;
}
