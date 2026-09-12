#include <stdio.h>
#include "./test.h"
#include <stdint.h>

void testTask(void);

uint8_t u8g_value[ 10 ];

/******************************************************************************/
/* @brief  Schedule function                                                  */
/* @param  None                                                               */
/* @note   This function calls the testTask function after printing "sch"     */
/******************************************************************************/
void sch( void )
{
    printf("sch\n");
    testTask();
}

void test( void )
{
    printf("test\n");
    sch();
    testTask();
}

void testTask( void )
{
    uint8_t u8_test;
    uint8_t u8_another;

    u8_test = (uint8_t)0;
    u8_another = (uint8_t)1;

    printf("testTask\n");
    printf("u8_test: %u\n", u8_test);
    printf("u8_another: %u\n", u8_another);
    printf("testTask again\n");

    if ( ( u8_test    == (uint8_t)0x00 )
      && ( u8_another == (uint8_t)0x01 ) )
    {
        printf("u8_test is zero\n");
        for ( uint8_t i = 0; i < (uint8_t)10; i++ )
        {
            (void)u8_test;
        }
    }
}

uint8_t u8_Encoder_GetValue( uint8_t u8_id )
{
    uint8_t u8t_value;
    u8t_value = u8g_value[ u8_id ];
    return u8t_value;
}
