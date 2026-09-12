#include <stdio.h> #include "./test.h"
#include <stdint.h>

void testTask( void );

uint8_t u8g_value[ 10 ];

uint8_t u8g_add_u8u8_u8( uint8_t u8t_a, uint8_t u8t_b )
{
    uint8_t u8t_result;

    u8t_result = u8t_a + u8t_b;

    return u8t_result;
}

/******************************************************************************/
/* @brief  Schedule function                                                  */
/* @param  None                                                               */
/* @note   This function calls the testTask function after printing "sch"     */
/******************************************************************************/
void sch( void )
{
    printf( "sch\n" );
    testTask();
}

void test( void )
{
    printf( "test\n" );
    sch();
    testTask();
}

void testTask( void )
{
    uint8_t u8_test;
    uint8_t u8_another;

    u8_test = (uint8_t)0;
    u8_another = (uint8_t)0x01;

    if ( ( u8_test == (uint8_t)0x00    )
      && ( u8_another == (uint8_t)0x01 ) )
    {
        for ( uint8_t i = 0; i < (uint8_t)10; i++ )
        {
            (void)u8_test;

            if ( u8g_value[ i ] == (uint8_t)0x00 )
            {

                return;
            }
        }
    }
}

uint8_t u8_Encoder_GetValue( uint8_t u8_id )
{
    uint8_t             u8t_value1;
    uint8_t u8t_value2;
    u8t_value = u8g_value[ u8_id ];
    return u8t_value;
}
