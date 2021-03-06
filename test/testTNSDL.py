import unittest
from hfcca_for_tnsdl import SDLTokenTranslator
from hfcca import UniversalAnalyzer, generate_tokens


class Test_sdl_hfcca(unittest.TestCase):
    def create_sdl_hfcca(self, source_code):
        return UniversalAnalyzer().analyze(SDLTokenTranslator().getFunctions(generate_tokens(source_code)) , "")
    def test_empty(self):
        result = self.create_sdl_hfcca("")
        self.assertEqual(0, len(result))
    def test_process(self):
        result = self.create_sdl_hfcca("PROCESS pofcap\n ENDPROCESS;")
        self.assertEqual(1, len(result))
        self.assertTrue('PROCESS pofcap' in result)
    def test_one_function(self):
        result = self.create_sdl_hfcca("PROCEDURE xxx\n ENDPROCEDURE;");
        self.assertEqual(1, len(result))
        self.assertTrue("PROCEDURE xxx" in result)
        self.assertEqual(1, result[0].cyclomatic_complexity)
        self.assertEqual(0, result[0].token_count)
    def test_one_function_with_condition(self):
        result = self.create_sdl_hfcca(example_sdl_procedure);
        self.assertEqual(1, len(result))
        self.assertTrue("PROCEDURE send_swo_msgs__r" in result)
        self.assertEqual(7, result[0].cyclomatic_complexity)
        self.assertEqual(173, result[0].token_count)
    def test_one_function_with_array(self):
        result = self.create_sdl_hfcca("""
        PROCEDURE send_swo_msgs__r;
        START;
            TASK array(0):= 1;
        ENDPROCEDURE;
        """);
        self.assertEqual(1, len(result))
        self.assertEqual(1, result[0].cyclomatic_complexity)
    def test_process_with_content(self):
        result = self.create_sdl_hfcca(example_sdl_process);
        self.assertEqual(5, len(result))
        self.assertTrue("PROCEDURE send_swo_msgs__r" in result)
        self.assertTrue("PROCESS pofsrt" in result)
        self.assertTrue("PROCESS pofsrt STATE start_state INPUT supervision_msg_s" in result)
        self.assertTrue("PROCESS pofsrt STATE start_state1 INPUT supervision_msg_s2" in result)
        self.assertEqual(2, result[1].cyclomatic_complexity)

example_sdl_procedure = '''
/**************************************************************************/
PROCEDURE send_swo_msgs__r;
/*
 * Send the given switchover message to POFFIC in all computers in the target list.
 **************************************************************************/
FPAR
    IN/OUT  targets  targets__t,
    IN      msg_num  message_number_t;

DCL
    i     dword := 0,
    c_i   dword,
    msg_group message_group_t,
    activity_signal byte := msg_attr_t_normal_priority_c,
    ppid  pid;

START;
    DECISION routing_state__pv;
    ( routing_state_t_active_c ):
       TASK activity_signal := msg_attr_t_is_active__c;
    ENDDECISION;

    TASK  ppid := SELF;
    WHILE i < targets.item_count;
       TASK  set_pid_computer_r( ppid, targets.target(i).addr );
       TASK  c_i := 0,
             msg_group := direct_delivery_gi;

       WHILE c_i < 2;
          DECISION targets.target(i).chan(c_i);
          ( T ):
             DECISION msg_num;
             ( NUMBER_FROM( pof_deny_messages_s )):
                OUTPUT pof_deny_messages_s TO ppid,
                       SET GROUP = msg_group;
             ( NUMBER_FROM( pof_allow_messages_s )):
                OUTPUT pof_allow_messages_s TO ppid,
                       SET GROUP = msg_group, PRIORITY = activity_signal;
             ENDDECISION;
          ENDDECISION;
          TASK c_i := c_i + 1,
               msg_group := rt_direct_delivery_gi;
       ENDWHILE;

       TASK i := i + 1;
    ENDWHILE;
ENDPROCEDURE send_swo_msgs__r;
'''

example_sdl_process = r'''
PROCESS pofsrt
  COMMENT '@(#)SID: POFSRTGX.SDL 2.1-0 06/07/11';
/*
 */

DCL
  addr_range addr_range_t;

PROCEDURE send_swo_msgs__r;
START;
    TASK  ppid := SELF;
ENDPROCEDURE send_swo_msgs__r;
START;
  /* announce to DMXRTE */
  DECISION post_office_announcement_r( post_district_index_t_atm_c,
           addr_range,
           pof_advisable_msg_len__c - sizeof(buffer_bottom_t),
           pof_ack_waiting_time__c  );
    ( success_ec ):
      TASK /* nop */;
    ELSE:
      TASK /* hanskat tiskiin */;
  ENDDECISION;
  NEXTSTATE start_state
    COMMENT 'Nuthin fancy here';

/******************************************************/
STATE start_state
  COMMENT 'Wait for the first supervision message';

  INPUT supervision_msg_s(*);
    OUTPUT supervision_ack_s( INPUT ) TO SENDER;
    TASK pofsrt__r; /* call the actual code */
    NEXTSTATE -; /* this is actually never reached */
ENDSTATE start_state
STATE start_state1
  COMMENT 'Wait for the first supervision message';

#if (tr)
  INPUT supervision_msg_s1(*);
    OUTPUT supervision_ack_s( INPUT ) TO SENDER;
    TASK pofsrt__r; /* call the actual code */
    NEXTSTATE -; /* this is actually never reached */
#endif
  INPUT INTERNAL supervision_msg_s2(*);
    OUTPUT supervision_ack_s( INPUT ) TO SENDER;
    TASK pofsrt__r; /* call the actual code */
    NEXTSTATE -; /* this is actually never reached */
ENDSTATE start_state
  COMMENT 'Hand prefix started';
ENDPROCESS pofsrt;
'''

