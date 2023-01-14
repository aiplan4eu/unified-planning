(define (domain someDomain)
	(:requirements :method-preconditions :equality :typing :hierarchy :negative-preconditions :universal-preconditions)
	(:types
		bus - vehicle
		shelter_leader - adult
		construction_crew - work_crew
		school - point
		power_van - vehicle
		transport_hub - point
		service_station - point
		hazardousness - object
		tow_truck - tree_or_tow_truck
		town - object
		police_van - vehicle
		mall - point
		snowplow - truck
		tree - object
		power_crew - work_crew
		ambulance - vehicle
		tree_crew - work_crew
		condition - object
		bus_driver - adult
		dump_truck - truck
		backhoe - truck
		emt_crew - adult
		hazard_team - work_crew
		child - person
		tree_truck - tree_or_tow_truck
		shelter - point
		university - point
		truck_driver - adult
		plowdriver - adult
		generator - object
		tree_or_tow_truck - truck
		tow_truck_driver - adult
		water_truck - truck
		truck - vehicle
		gas_can - object
		powerco - callable
		car - vehicle
		vehicle - object
		hospital - point
		waterco - callable
		callable - object
		park - point
		police_unit - adult
		food - object
		garbage_dump - dump
		dump - point
		point - object
		water_crew - work_crew
		work_crew - adult
		adult - person
		person - object
	)
        (:constants

                fema - callable
                ebs - callable
                police_chief - callable
                very_hazardous - hazardousness
        )


	(:predicates
		(atloc ?arg0 - object ?arg1 - point)
		(in_vehicle ?arg0 - object ?arg1 - vehicle)
		(can_drive ?arg0 - adult ?arg1 - vehicle)
		(can_lift ?arg0 - person ?arg1 - object)
		(fit_in ?arg0 - object ?arg1 - vehicle)
		(has_condition ?arg0 - person ?arg1 - condition)
		(hazard_seriousness ?arg0 - point ?arg1 - point ?arg2 - hazardousness)
		(hospital_doesnt_treat ?arg0 - hospital ?arg1 - condition)
		(in_town ?arg0 - point ?arg1 - town)
		(no_electricity ?arg0 - point)
		(powerco_of ?arg0 - town ?arg1 - powerco)
		(road_snowy ?arg0 - point ?arg1 - point)
		(serious_condition ?arg0 - condition)
		(tree_blocking_road ?arg0 - point ?arg1 - point ?arg2 - tree)
		(waterco_of ?arg0 - town ?arg1 - waterco)
		(wrecked_vehicle ?arg0 - point ?arg1 - point ?arg2 - vehicle)
		(l1)
		(l2)
	)
		(:task tlt
    :parameters ()
	)
	(:task set_up_shelter
		:parameters (?p0 - point)
	)
	(:task fix_water_main
		:parameters (?p0 - point ?p1 - point)
	)
	(:task clear_road_hazard
		:parameters (?p0 - point ?p1 - point)
	)
	(:task clear_road_wreck
		:parameters (?p0 - point ?p1 - point)
	)
	(:task clear_road_tree
		:parameters (?p0 - point ?p1 - point)
	)
	(:task plow_road
		:parameters (?p0 - point ?p1 - point)
	)
	(:task quell_riot
		:parameters (?p0 - point)
	)
	(:task provide_temp_heat
		:parameters (?p0 - person)
	)
	(:task fix_power_line
		:parameters (?p0 - point)
	)
	(:task provide_medical_attention
		:parameters (?p0 - person)
	)
	(:task turn_on_power
		:parameters (?p0 - power_crew ?p1 - point)
	)
	(:task clear_tree
		:parameters (?t0 - tree)
	)
	(:task close_hole
		:parameters (?u0 - point ?u1 - point)
	)
	(:task clear_wreck
		:parameters (?p0 - point ?p1 - point)
	)
	(:task set_up_cones
		:parameters (?p0 - point ?p1 - point)
	)
	(:task get_in
		:parameters (?o0 - object ?v1 - vehicle)
	)
	(:task get_to
		:parameters (?o0 - object ?p1 - point)
	)
	(:task remove_blockage
		:parameters (?t0 - tree)
	)
	(:task block_road
		:parameters (?p0 - point ?p1 - point)
	)
	(:task take_down_cones
		:parameters (?p0 - point ?p1 - point)
	)
	(:task shut_off_power
		:parameters (?p0 - power_crew ?p1 - point)
	)
	(:task open_hole
		:parameters (?p0 - point ?p1 - point)
	)
	(:task declare_curfew
		:parameters (?t0 - town)
	)
	(:task turn_on_water
		:parameters (?p0 - point ?p1 - point)
	)
	(:task shut_off_water
		:parameters (?p0 - point ?p1 - point)
	)
	(:task clean_up_hazard
		:parameters (?p0 - point ?p1 - point)
	)
	(:task drive_to
		:parameters (?p0 - person ?v1 - vehicle ?p2 - point)
	)
	(:task stabilize
		:parameters (?o0 - object)
	)
	(:task unblock_road
		:parameters (?p0 - point ?p1 - point)
	)
	(:task tow_to
		:parameters (?v0 - vehicle ?g1 - garbage_dump)
	)
	(:task repair_line
		:parameters (?p0 - power_crew ?p1 - point)
	)
	(:task add_fuel
		:parameters (?s0 - service_station ?o1 - object)
	)
	(:task get_out
		:parameters (?o0 - object ?v1 - vehicle)
	)
	(:task repair_pipe
		:parameters (?p0 - point ?p1 - point)
	)
	(:task get_electricity
		:parameters (?p0 - point)
	)
	(:task generate_temp_electricity
		:parameters (?p0 - point)
	)
	(:task emt_treat
		:parameters (?o0 - object)
	)
	(:task make_full_fuel
		:parameters (?g0 - generator)
	)
	(:task ccall
		:parameters (?place - callable)
	)
		
(:method m_tlt_set_up_shelter
    :parameters (?p0 - point)
    :task (tlt)
		:subtasks (and
		 (task0 (set_up_shelter ?p0))
		)
	)
	(:method m_tlt_fix_water_main
		:parameters (?p0 - point ?p1 - point)
		:task (tlt)
		:subtasks (and
		 (task0 (fix_water_main ?p0 ?p1))
		)
	)
	(:method m_tlt_clear_road_hazard
		:parameters (?p0 - point ?p1 - point)
		:task (tlt)
		:subtasks (and
		 (task0 (clear_road_hazard ?p0 ?p1))
		)
	)
	(:method m_tlt_clear_road_wreck
		:parameters (?p0 - point ?p1 - point)
		:task (tlt)
		:subtasks (and
		 (task0 (clear_road_wreck ?p0 ?p1))
		)
	)
	(:method m_tlt_clear_road_tree
		:parameters (?p0 - point ?p1 - point)
		:task (tlt)
		:subtasks (and
		 (task0 (clear_road_tree ?p0 ?p1))
		)
	)
	(:method m_tlt_plow_road
		:parameters (?p0 - point ?p1 - point)
		:task (tlt)
		:subtasks (and
		 (task0 (plow_road ?p0 ?p1))
		)
	)
	(:method m_tlt_quell_riot
		:parameters (?p0 - point)
		:task (tlt)
		:subtasks (and
		 (task0 (quell_riot ?p0))
		)
	)
	(:method m_tlt_provide_temp_heat
		:parameters (?p0 - person)
		:task (tlt)
		:subtasks (and
		 (task0 (provide_temp_heat ?p0))
		)
	)
	(:method m_tlt_fix_power_line
		:parameters (?p0 - point)
		:task (tlt)
		:subtasks (and
		 (task0 (fix_power_line ?p0))
		)
	)
	(:method m_tlt_provide_medical_attention
		:parameters (?p0 - person)
		:task (tlt)
		:subtasks (and
		 (task0 (provide_medical_attention ?p0))
		)
	)
	(:method m_set_up_shelter
		:parameters (?food - food ?leader - shelter_leader ?loc - point)
		:task (set_up_shelter ?loc)
		:subtasks (and
		 (task0 (get_electricity ?loc))
		 (task1 (get_to ?leader ?loc))
		 (task2 (get_to ?food ?loc))
		)
		:ordering (and
			(< task0 task1)
			(< task1 task2)
		)
	)
	(:method m_fix_water_main
		:parameters (?from - point ?to - point)
		:task (fix_water_main ?from ?to)
		:subtasks (and
		 (task0 (shut_off_water ?from ?to))
		 (task1 (repair_pipe ?from ?to))
		 (task2 (turn_on_water ?from ?to))
		)
		:ordering (and
			(< task0 task1)
			(< task1 task2)
		)
	)
	(:method m_clear_road_hazard
		:parameters (?from - point ?to - point)
		:task (clear_road_hazard ?from ?to)
		:subtasks (and
		 (task0 (block_road ?from ?to))
		 (task1 (clean_up_hazard ?from ?to))
		 (task2 (unblock_road ?from ?to))
		)
		:ordering (and
			(< task0 task1)
			(< task1 task2)
		)
	)
	(:method m_clear_road_wreck
		:parameters (?from - point ?to - point)
		:task (clear_road_wreck ?from ?to)
		:subtasks (and
		 (task0 (set_up_cones ?from ?to))
		 (task1 (clear_wreck ?from ?to))
		 (task2 (take_down_cones ?from ?to))
		)
		:ordering (and
			(< task0 task1)
			(< task1 task2)
		)
	)
	(:method m_clear_road_tree
		:parameters (?from - point ?to - point ?tree - tree)
		:task (clear_road_tree ?from ?to)
		:subtasks (and
		 (task0 (set_up_cones ?from ?to))
		 (task1 (clear_tree ?tree))
		 (task2 (take_down_cones ?from ?to))
		 (task3 (SHOP_methodm_clear_road_tree_precondition ?from ?to ?tree))
		)
		:ordering (and
			(< task3 task0)
			(< task0 task1)
			(< task1 task2)
		)
	)
	(:method m_plow_road
		:parameters (?driver - plowdriver ?from - point ?plow - snowplow ?plowloc - point ?to - point)
		:task (plow_road ?from ?to)
		:subtasks (and
		 (task0 (get_to ?driver ?plowloc))
		 (task1 (navegate_snowplow ?driver ?plow ?from))
		 (task2 (engage_plow ?driver ?plow))
		 (task3 (navegate_snowplow ?driver ?plow ?to))
		 (task4 (disengage_plow ?driver ?plow))
		 (task5 (SHOP_methodm_plow_road_precondition ?from ?to ?plow ?plowloc))
		)
		:ordering (and
			(< task5 task0)
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
			(< task3 task4)
		)
	)
	(:method m_quell_riot
		:parameters (?loc - point ?p1 - police_unit ?p2 - police_unit ?town - town)
		:task (quell_riot ?loc)
		:subtasks (and
		 (task0 (declare_curfew ?town))
		 (task1 (get_to ?p1 ?loc))
		 (task2 (get_to ?p2 ?loc))
		 (task3 (set_up_barricades ?p1))
		 (task4 (set_up_barricades ?p2))
		 (task5 (SHOP_methodm_quell_riot_precondition ?loc ?town))
		)
		:ordering (and
			(< task5 task0)
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
			(< task3 task4)
		)
		:constraints (and
			(not (= ?p1 ?p2))
		)
	)
	(:method m_provide_temp_heat_to_shelter
		:parameters (?person - person ?shelter - shelter)
		:task (provide_temp_heat ?person)
		:subtasks (and
		 (task0 (get_to ?person ?shelter))
		)
	)
	(:method m_provide_temp_heat_local_electricity
		:parameters (?person - person ?ploc - point)
		:task (provide_temp_heat ?person)
		:subtasks (and
		 (task0 (generate_temp_electricity ?ploc))
		 (task1 (turn_on_heat ?ploc))
		 (task2 (SHOP_methodm_provide_temp_heat_local_electricity_precondition ?person ?ploc))
		)
		:ordering (and
			(< task2 task0)
			(< task0 task1)
		)
	)
	(:method m_fix_power_line
		:parameters (?crew - power_crew ?lineloc - point ?van - power_van)
		:task (fix_power_line ?lineloc)
		:subtasks (and
		 (task0 (get_to ?crew ?lineloc))
		 (task1 (get_to ?van ?lineloc))
		 (task2 (repair_line ?crew ?lineloc))
		)
		:ordering (and
			(< task0 task1)
			(< task1 task2)
		)
	)
	(:method m_provide_medical_attention_in_hospital
		:parameters (?cond - condition ?hosp - hospital ?person - person)
		:task (provide_medical_attention ?person)
		:subtasks (and
		 (task0 (get_to ?person ?hosp))
		 (task1 (treat_in_hospital ?person ?hosp))
		 (task2 (SHOP_methodm_provide_medical_attention_in_hospital_precondition ?person ?cond ?hosp))
		)
		:ordering (and
			(< task2 task0)
			(< task0 task1)
		)
	)
	(:method m_provide_medical_attention_simple_on_site
		:parameters (?cond - condition ?person - person)
		:task (provide_medical_attention ?person)
		:subtasks (and
		 (task0 (emt_treat ?person))
		 (task1 (SHOP_methodm_provide_medical_attention_simple_on_site_precondition ?person ?cond))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_clean_up_hazard_very_hazardous
		:parameters (?from - point ?to - point)
		:task (clean_up_hazard ?from ?to)
		:subtasks (and
		 (task0 (ccall fema))
		 (task1 (SHOP_methodm_clean_up_hazard_very_hazardous_precondition ?from ?to very_hazardous))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_clean_up_hazard_normal
		:parameters (?from - point ?h_compiled_1_ps3 - hazardousness ?ht - hazard_team ?to - point)
		:task (clean_up_hazard ?from ?to)
		:subtasks (and
		 (task0 (get_to ?ht ?from))
		 (task1 (clean_hazard ?ht ?from ?to ?h_compiled_1_ps3))
		 (task2 (SHOP_methodm_clean_up_hazard_normal_precondition ?from ?to very_hazardous))
		)
		:ordering (and
			(< task2 task0)
			(< task0 task1)
		)
	)
	(:method m_block_road
		:parameters (?from - point ?police - police_unit ?to - point)
		:task (block_road ?from ?to)
		:subtasks (and
		 (task0 (set_up_cones ?from ?to))
		 (task1 (get_to ?police ?from))
		)
	)
	(:method m_unblock_road
		:parameters (?from - point ?to - point)
		:task (unblock_road ?from ?to)
		:subtasks (and
		 (task0 (take_down_cones ?from ?to))
		)
	)
	(:method m_get_electricity_noop
		:parameters (?loc - point)
		:task (get_electricity ?loc)
		:subtasks (and
		 (task0 (SHOP_methodm_get_electricity_noop_precondition ?loc))
		)
	)
	(:method m_get_electricity
		:parameters (?loc - point)
		:task (get_electricity ?loc)
		:subtasks (and
		 (task0 (generate_temp_electricity ?loc))
		 (task1 (SHOP_methodm_get_electricity_precondition ?loc))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_repair_pipe
		:parameters (?crew - water_crew ?from - point ?to - point)
		:task (repair_pipe ?from ?to)
		:subtasks (and
		 (task0 (get_to ?crew ?from))
		 (task1 (set_up_cones ?from ?to))
		 (task2 (open_hole ?from ?to))
		 (task3 (replace_pipe ?crew ?from ?to))
		 (task4 (close_hole ?from ?to))
		 (task5 (take_down_cones ?from ?to))
		)
		:ordering (and
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
			(< task3 task4)
			(< task4 task5)
		)
	)
	(:method m_open_hole
		:parameters (?backhoe - backhoe ?from - point ?to - point)
		:task (open_hole ?from ?to)
		:subtasks (and
		 (task0 (get_to ?backhoe ?from))
		 (task1 (dig ?backhoe ?from))
		)
		:ordering (and
			(< task0 task1)
		)
	)
	(:method m_close_hole
		:parameters (?backhoe - backhoe ?from - point ?to - point)
		:task (close_hole ?from ?to)
		:subtasks (and
		 (task0 (get_to ?backhoe ?from))
		 (task1 (fill_in ?backhoe ?from))
		)
		:ordering (and
			(< task0 task1)
		)
	)
	(:method m_set_up_cones
		:parameters (?crew - work_crew ?from - point ?to - point)
		:task (set_up_cones ?from ?to)
		:subtasks (and
		 (task0 (get_to ?crew ?from))
		 (task1 (place_cones ?crew))
		)
		:ordering (and
			(< task0 task1)
		)
	)
	(:method m_take_down_cones
		:parameters (?crew - work_crew ?from - point ?to - point)
		:task (take_down_cones ?from ?to)
		:subtasks (and
		 (task0 (get_to ?crew ?from))
		 (task1 (pickup_cones ?crew))
		)
		:ordering (and
			(< task0 task1)
		)
	)
	(:method m_clear_wreck
		:parameters (?dump - garbage_dump ?from - point ?to - point ?veh - vehicle)
		:task (clear_wreck ?from ?to)
		:subtasks (and
		 (task0 (tow_to ?veh ?dump))
		 (task1 (SHOP_methodm_clear_wreck_precondition ?from ?to ?veh))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_tow_to
		:parameters (?to - garbage_dump ?ttruck - tow_truck ?veh - vehicle ?vehloc - point)
		:task (tow_to ?veh ?to)
		:subtasks (and
		 (task0 (get_to ?ttruck ?vehloc))
		 (task1 (hook_to_tow_truck ?ttruck ?veh))
		 (task2 (get_to ?ttruck ?to))
		 (task3 (unhook_from_tow_truck ?ttruck ?veh))
		 (task4 (SHOP_methodm_tow_to_precondition ?veh ?vehloc))
		)
		:ordering (and
			(< task4 task0)
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
		)
	)
	(:method m_clear_tree
		:parameters (?tcrew - tree_crew ?tree - tree ?treeloc - point)
		:task (clear_tree ?tree)
		:subtasks (and
		 (task0 (get_to ?tcrew ?treeloc))
		 (task1 (cut_tree ?tcrew ?tree))
		 (task2 (remove_blockage ?tree))
		 (task3 (SHOP_methodm_clear_tree_precondition ?tree ?treeloc))
		)
		:ordering (and
			(< task3 task0)
			(< task0 task1)
			(< task1 task2)
		)
	)
	(:method m_remove_blockage_move_to_side_of_street
		:parameters (?crew - work_crew ?loc - point ?stuff - tree)
		:task (remove_blockage ?stuff)
		:subtasks (and
		 (task0 (get_to ?crew ?loc))
		 (task1 (carry_blockage_out_of_way ?crew ?stuff))
		 (task2 (SHOP_methodm_remove_blockage_move_to_side_of_street_precondition ?stuff ?loc))
		)
		:ordering (and
			(< task2 task0)
			(< task0 task1)
		)
	)
	(:method m_remove_blockage_carry_away
		:parameters (?dump - garbage_dump ?stuff - tree)
		:task (remove_blockage ?stuff)
		:subtasks (and
		 (task0 (get_to ?stuff ?dump))
		)
	)
	(:method m_declare_curfew
		:parameters (?town - town)
		:task (declare_curfew ?town)
		:subtasks (and
		 (task0 (ccall ebs))
		 (task1 (ccall police_chief))
		)
	)
	(:method m_generate_temp_electricity
		:parameters (?gen - generator ?loc - point)
		:task (generate_temp_electricity ?loc)
		:subtasks (and
		 (task0 (make_full_fuel ?gen))
		 (task1 (get_to ?gen ?loc))
		 (task2 (hook_up ?gen ?loc))
		 (task3 (turn_on ?gen))
		)
		:ordering (and
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
		)
	)
	(:method m_make_full_fuel_with_gas_can
		:parameters (?gc - gas_can ?gen - generator ?genloc - point ?ss - service_station)
		:task (make_full_fuel ?gen)
		:subtasks (and
		 (task0 (get_to ?gc ?ss))
		 (task1 (add_fuel ?ss ?gc))
		 (task2 (get_to ?gc ?genloc))
		 (task3 (pour_into ?gc ?gen))
		 (task4 (SHOP_methodm_make_full_fuel_with_gas_can_precondition ?gen ?genloc))
		)
		:ordering (and
			(< task4 task0)
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
		)
	)
	(:method m_make_full_fuel_at_service_station
		:parameters (?gen - generator ?ss - service_station)
		:task (make_full_fuel ?gen)
		:subtasks (and
		 (task0 (get_to ?gen ?ss))
		 (task1 (add_fuel ?ss ?gen))
		)
		:ordering (and
			(< task0 task1)
		)
	)
	(:method m_add_fuel
		:parameters (?obj - generator ?ss - service_station)
		:task (add_fuel ?ss ?obj)
		:subtasks (and
		 (task0 (pay ?ss))
		 (task1 (pump_gas_into ?ss ?obj))
		)
	)
	(:method m_repair_line_with_tree
		:parameters (?crew - power_crew ?lineloc - point ?tree - tree)
		:task (repair_line ?crew ?lineloc)
		:subtasks (and
		 (task0 (shut_off_power ?crew ?lineloc))
		 (task1 (clear_tree ?tree))
		 (task2 (remove_wire ?crew ?lineloc))
		 (task3 (string_wire ?crew ?lineloc))
		 (task4 (turn_on_power ?crew ?lineloc))
		 (task5 (SHOP_methodm_repair_line_with_tree_precondition ?tree ?lineloc ?crew))
		)
		:ordering (and
			(< task5 task0)
			(< task0 task1)
			(< task0 task2)
			(< task1 task3)
			(< task2 task3)
			(< task3 task4)
		)
	)
	(:method m_repair_line_without_tree
		:parameters (?crew - power_crew ?lineloc - point)
		:task (repair_line ?crew ?lineloc)
		:subtasks (and
		 (task0 (shut_off_power ?crew ?lineloc))
		 (task1 (remove_wire ?crew ?lineloc))
		 (task2 (string_wire ?crew ?lineloc))
		 (task3 (turn_on_power ?crew ?lineloc))
		 (task4 (SHOP_methodm_repair_line_without_tree_precondition ?lineloc ?crew))
		)
		:ordering (and
			(< task4 task0)
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
		)
	)
	(:method m_shut_off_power
		:parameters (?crew - power_crew ?loc - point ?powerco - powerco ?town - town)
		:task (shut_off_power ?crew ?loc)
		:subtasks (and
		 (task0 (ccall ?powerco))
		 (task1 (SHOP_methodm_shut_off_power_precondition ?loc ?town ?powerco))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_turn_on_power
		:parameters (?crew - power_crew ?loc - point ?powerco - powerco ?town - town)
		:task (turn_on_power ?crew ?loc)
		:subtasks (and
		 (task0 (ccall ?powerco))
		 (task1 (SHOP_methodm_turn_on_power_precondition ?loc ?town ?powerco))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_shut_off_water
		:parameters (?from - point ?to - point ?town - town ?waterco - waterco)
		:task (shut_off_water ?from ?to)
		:subtasks (and
		 (task0 (ccall ?waterco))
		 (task1 (SHOP_methodm_shut_off_water_precondition ?from ?town ?waterco))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_turn_on_water
		:parameters (?from - point ?to - point ?town - town ?waterco - waterco)
		:task (turn_on_water ?from ?to)
		:subtasks (and
		 (task0 (ccall ?waterco))
		 (task1 (SHOP_methodm_turn_on_water_precondition ?from ?town ?waterco))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_emt_treat
		:parameters (?emt - emt_crew ?person - person ?personloc - point)
		:task (emt_treat ?person)
		:subtasks (and
		 (task0 (get_to ?emt ?personloc))
		 (task1 (treat ?emt ?person ?personloc))
		 (task2 (SHOP_methodm_emt_treat_precondition ?person ?personloc))
		)
		:ordering (and
			(< task2 task0)
			(< task0 task1)
		)
	)
	(:method m_stabilize
		:parameters (?person - person)
		:task (stabilize ?person)
		:subtasks (and
		 (task0 (emt_treat ?person))
		)
	)
	(:method m_get_to_already_there
		:parameters (?obj - object ?place - point)
		:task (get_to ?obj ?place)
		:subtasks (and
		 (task0 (SHOP_methodm_get_to_already_there_precondition ?obj ?place))
		)
	)
	(:method m_get_to_person_drives_themself
		:parameters (?person - person ?place - point ?veh - vehicle ?vehloc - point)
		:task (get_to ?person ?place)
		:subtasks (and
		 (task0 (drive_to ?person ?veh ?place))
		 (task1 (SHOP_methodm_get_to_person_drives_themself_precondition ?person ?place ?veh ?vehloc))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_get_to_vehicle_gets_driven
		:parameters (?person - person ?place - point ?veh - vehicle ?vehloc - point)
		:task (get_to ?veh ?place)
		:subtasks (and
		 (task0 (drive_to ?person ?veh ?place))
		 (task1 (SHOP_methodm_get_to_vehicle_gets_driven_precondition ?veh ?place ?vehloc ?person))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_get_to_as_cargo
		:parameters (?obj - object ?objloc - point ?place - point ?veh - vehicle)
		:task (get_to ?obj ?place)
		:subtasks (and
		 (task0 (get_to ?veh ?objloc))
		 (task1 (get_in ?obj ?veh))
		 (task2 (get_to ?veh ?place))
		 (task3 (get_out ?obj ?veh))
		 (task4 (SHOP_methodm_get_to_as_cargo_precondition ?obj ?place ?objloc ?veh))
		)
		:ordering (and
			(< task4 task0)
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
		)
	)
	(:method m_get_to_with_ambulance
		:parameters (?obj - person ?objloc - point ?place - point ?veh - ambulance)
		:task (get_to ?obj ?place)
		:subtasks (and
		 (task0 (get_to ?veh ?objloc))
		 (task1 (stabilize ?obj))
		 (task2 (get_in ?obj ?veh))
		 (task3 (get_to ?veh ?place))
		 (task4 (get_out ?obj ?veh))
		 (task5 (SHOP_methodm_get_to_with_ambulance_precondition ?obj ?place ?objloc ?veh))
		)
		:ordering (and
			(< task5 task0)
			(< task0 task1)
			(< task1 task2)
			(< task2 task3)
			(< task3 task4)
		)
	)
	(:method m_drive_to
		:parameters (?loc - point ?person - adult ?veh - vehicle ?vehloc - point)
		:task (drive_to ?person ?veh ?loc)
		:subtasks (and
		 (task0 (navegate_vehicle ?person ?veh ?loc ?vehloc))
		 (task1 (SHOP_methodm_drive_to_precondition ?veh ?vehloc ?person))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_get_in_ambulatory_person
		:parameters (?obj - person ?objloc - point ?veh - vehicle)
		:task (get_in ?obj ?veh)
		:subtasks (and
		 (task0 (climb_in ?obj ?veh ?objloc))
		 (task1 (SHOP_methodm_get_in_ambulatory_person_precondition ?obj ?objloc ?veh))
		)
		:ordering (and
			(< task1 task0)
		)
	)
	(:method m_get_in_load_in
		:parameters (?obj - object ?objloc - point ?person - person ?veh - vehicle)
		:task (get_in ?obj ?veh)
		:subtasks (and
		 (task0 (get_to ?person ?objloc))
		 (task1 (load ?person ?obj ?veh ?objloc))
		 (task2 (SHOP_methodm_get_in_load_in_precondition ?obj ?objloc ?veh ?person))
		)
		:ordering (and
			(< task2 task0)
			(< task0 task1)
		)
	)
	(:method m_get_out_ambulatory_person
		:parameters (?obj - person ?p - point ?veh - vehicle)
		:task (get_out ?obj ?veh)
		:subtasks (and
		 (task0 (climb_out ?obj ?veh ?p))
		)
	)
	(:method m_get_out_unload
		:parameters (?obj - object ?person - person ?veh - vehicle ?vehloc - point)
		:task (get_out ?obj ?veh)
		:subtasks (and
		 (task0 (get_to ?person ?vehloc))
		 (task1 (unload ?person ?obj ?veh ?vehloc))
		 (task2 (SHOP_methodm_get_out_unload_precondition ?veh ?vehloc ?person ?obj))
		)
		:ordering (and
			(< task2 task0)
			(< task0 task1)
		)
	)
	(:method regular_1
		:parameters (?place - callable)
		:task (ccall ?place)
		:subtasks (and
		 (task0 (call ?place))
		)
	)
	(:method prefix_1
		:parameters (?place - callable)
		:task (ccall ?place)
		:precondition (and
			(= ?place police_chief)
		)
		:subtasks (and
		 (task0 (p_1Call))
		)
	)
	(:action navegate_snowplow
		:parameters (?person - plowdriver ?veh - snowplow ?loc - point)
		:precondition 
()
	)
	(:action engage_plow
		:parameters (?person - plowdriver ?plow - snowplow)
		:precondition 
()
	)
	(:action disengage_plow
		:parameters (?person - plowdriver ?plow - snowplow)
		:precondition 
()
	)
	(:action navegate_vehicle
		:parameters (?person - adult ?veh - vehicle ?loc - point ?vehloc - point)
		:precondition 
			(and
				(atloc ?veh ?vehloc)
				(atloc ?person ?vehloc)
				(can_drive ?person ?veh)
			)
		:effect
			(and
				(atloc ?veh ?loc)
				(atloc ?person ?loc)
				(not (atloc ?veh ?vehloc))
				(not (atloc ?person ?vehloc))
			)
	)
	(:action climb_in
		:parameters (?obj - person ?veh - vehicle ?objloc - point)
		:precondition 
			(and
				(atloc ?obj ?objloc)
				(atloc ?veh ?objloc)
				(fit_in ?obj ?veh)
			)
		:effect
			(and
				(in_vehicle ?obj ?veh)
				(not (atloc ?obj ?objloc))
			)
	)
	(:action climb_out
		:parameters (?obj - person ?veh - vehicle ?vehloc - point)
		:precondition 
			(and
				(in_vehicle ?obj ?veh)
				(atloc ?veh ?vehloc)
			)
		:effect
			(and
				(atloc ?obj ?vehloc)
				(not (in_vehicle ?obj ?veh))
			)
	)
	(:action load
		:parameters (?person - person ?obj - object ?veh - vehicle ?objloc - point)
		:precondition 
			(and
				(atloc ?obj ?objloc)
				(atloc ?veh ?objloc)
				(atloc ?person ?objloc)
				(fit_in ?obj ?veh)
				(can_lift ?person ?obj)
			)
		:effect
			(and
				(in_vehicle ?obj ?veh)
				(not (atloc ?obj ?objloc))
			)
	)
	(:action unload
		:parameters (?person - person ?obj - object ?veh - vehicle ?vehloc - point)
		:precondition 
			(and
				(in_vehicle ?obj ?veh)
				(atloc ?veh ?vehloc)
				(atloc ?person ?vehloc)
				(can_lift ?person ?obj)
			)
		:effect
			(and
				(atloc ?obj ?vehloc)
				(not (in_vehicle ?obj ?veh))
			)
	)
	(:action treat
		:parameters (?emt - emt_crew ?person - person ?ploc - point)
		:precondition 
			(and
				(atloc ?person ?ploc)
				(atloc ?emt ?ploc)
			)
	)
	(:action treat_in_hospital
		:parameters (?person - person ?hospital - hospital)
		:precondition 
()
	)
	(:action call
		:parameters (?place - callable)
		:precondition 
()
	)
	(:action remove_wire
		:parameters (?crew - power_crew ?lineloc - point)
		:precondition 
()
	)
	(:action string_wire
		:parameters (?crew - power_crew ?lineloc - point)
		:precondition 
()
	)
	(:action carry_blockage_out_of_way
		:parameters (?crew - work_crew ?stuff - tree)
		:precondition 
()
	)
	(:action cut_tree
		:parameters (?crew - tree_crew ?tree - tree)
		:precondition 
()
	)
	(:action hook_up
		:parameters (?gen - generator ?loc - point)
		:precondition 
()
	)
	(:action pour_into
		:parameters (?can - gas_can ?gen - generator)
		:precondition 
()
	)
	(:action turn_on
		:parameters (?gen - generator)
		:precondition 
()
	)
	(:action pay
		:parameters (?loc - service_station)
		:precondition 
()
	)
	(:action pump_gas_into
		:parameters (?loc - service_station ?gen - generator)
		:precondition 
()
	)
	(:action turn_on_heat
		:parameters (?loc - point)
		:precondition 
()
	)
	(:action set_up_barricades
		:parameters (?police - police_unit)
		:precondition 
()
	)
	(:action place_cones
		:parameters (?police - work_crew)
		:precondition 
()
	)
	(:action pickup_cones
		:parameters (?police - work_crew)
		:precondition 
()
	)
	(:action hook_to_tow_truck
		:parameters (?ttruck - tow_truck ?veh - vehicle)
		:precondition 
()
	)
	(:action unhook_from_tow_truck
		:parameters (?ttruck - tow_truck ?veh - vehicle)
		:precondition 
()
	)
	(:action dig
		:parameters (?backhoe - backhoe ?place - point)
		:precondition 
()
	)
	(:action fill_in
		:parameters (?backhoe - backhoe ?place - point)
		:precondition 
()
	)
	(:action replace_pipe
		:parameters (?crew - water_crew ?from - point ?to - point)
		:precondition 
()
	)
	(:action clean_hazard
		:parameters (?hazard_team - hazard_team ?from - point ?to - point ?h_compiled_1 - hazardousness)
		:precondition 
			(and
				(hazard_seriousness ?from ?to ?h_compiled_1)
				(not (hazard_seriousness ?from ?to very_hazardous))
			)
	)
	(:action p_1Call
		:parameters ()
		:precondition 
			(and
				(l1)
			)
		:effect
			(and
				(l2)
				(not (l1))
			)
	)
	(:action SHOP_methodm_clear_road_tree_precondition
		:parameters (?from - point ?to - point ?tree - tree)
		:precondition 
			(and
				(tree_blocking_road ?from ?to ?tree)
			)
	)
	(:action SHOP_methodm_plow_road_precondition
		:parameters (?from - point ?to - point ?plow - snowplow ?plowloc - point)
		:precondition 
			(and
				(road_snowy ?from ?to)
				(atloc ?plow ?plowloc)
			)
	)
	(:action SHOP_methodm_quell_riot_precondition
		:parameters (?loc - point ?town - town)
		:precondition 
			(and
				(in_town ?loc ?town)
			)
	)
	(:action SHOP_methodm_provide_temp_heat_local_electricity_precondition
		:parameters (?person - person ?ploc - point)
		:precondition 
			(and
				(atloc ?person ?ploc)
			)
	)
	(:action SHOP_methodm_provide_medical_attention_in_hospital_precondition
		:parameters (?person - person ?cond - condition ?hosp - hospital)
		:precondition 
			(and
				(has_condition ?person ?cond)
				(not (hospital_doesnt_treat ?hosp ?cond))
			)
	)
	(:action SHOP_methodm_provide_medical_attention_simple_on_site_precondition
		:parameters (?person - person ?cond - condition)
		:precondition 
			(and
				(has_condition ?person ?cond)
				(not (serious_condition ?cond))
			)
	)
	(:action SHOP_methodm_clean_up_hazard_very_hazardous_precondition
		:parameters (?from - point ?to - point ?varToConstConstant_very_hazardous_ - hazardousness)
		:precondition 
			(and
				(hazard_seriousness ?from ?to ?varToConstConstant_very_hazardous_)
			)
	)
	(:action SHOP_methodm_clean_up_hazard_normal_precondition
		:parameters (?from - point ?to - point ?varToConstConstant_very_hazardous_ - hazardousness)
		:precondition 
			(and
				(not (hazard_seriousness ?from ?to ?varToConstConstant_very_hazardous_))
			)
	)
	(:action SHOP_methodm_get_electricity_noop_precondition
		:parameters (?loc - point)
		:precondition 
			(and
				(not (no_electricity ?loc))
			)
	)
	(:action SHOP_methodm_get_electricity_precondition
		:parameters (?loc - point)
		:precondition 
			(and
				(no_electricity ?loc)
			)
	)
	(:action SHOP_methodm_clear_wreck_precondition
		:parameters (?from - point ?to - point ?veh - vehicle)
		:precondition 
			(and
				(wrecked_vehicle ?from ?to ?veh)
			)
	)
	(:action SHOP_methodm_tow_to_precondition
		:parameters (?veh - vehicle ?vehloc - point)
		:precondition 
			(and
				(atloc ?veh ?vehloc)
			)
	)
	(:action SHOP_methodm_clear_tree_precondition
		:parameters (?tree - tree ?treeloc - point)
		:precondition 
			(and
				(atloc ?tree ?treeloc)
			)
	)
	(:action SHOP_methodm_remove_blockage_move_to_side_of_street_precondition
		:parameters (?stuff - tree ?loc - point)
		:precondition 
			(and
				(atloc ?stuff ?loc)
			)
	)
	(:action SHOP_methodm_make_full_fuel_with_gas_can_precondition
		:parameters (?gen - generator ?genloc - point)
		:precondition 
			(and
				(atloc ?gen ?genloc)
			)
	)
	(:action SHOP_methodm_repair_line_with_tree_precondition
		:parameters (?tree - tree ?lineloc - point ?crew - power_crew)
		:precondition 
			(and
				(atloc ?tree ?lineloc)
				(atloc ?crew ?lineloc)
			)
	)
	(:action SHOP_methodm_repair_line_without_tree_precondition
		:parameters (?lineloc - point ?crew - power_crew)
		:precondition 
			(and
				(forall (?tree - tree)
					(not (atloc ?tree ?lineloc))
				)
				(atloc ?crew ?lineloc)
			)
	)
	(:action SHOP_methodm_shut_off_power_precondition
		:parameters (?loc - point ?town - town ?powerco - powerco)
		:precondition 
			(and
				(in_town ?loc ?town)
				(powerco_of ?town ?powerco)
			)
	)
	(:action SHOP_methodm_turn_on_power_precondition
		:parameters (?loc - point ?town - town ?powerco - powerco)
		:precondition 
			(and
				(in_town ?loc ?town)
				(powerco_of ?town ?powerco)
			)
	)
	(:action SHOP_methodm_shut_off_water_precondition
		:parameters (?from - point ?town - town ?waterco - waterco)
		:precondition 
			(and
				(in_town ?from ?town)
				(waterco_of ?town ?waterco)
			)
	)
	(:action SHOP_methodm_turn_on_water_precondition
		:parameters (?from - point ?town - town ?waterco - waterco)
		:precondition 
			(and
				(in_town ?from ?town)
				(waterco_of ?town ?waterco)
			)
	)
	(:action SHOP_methodm_emt_treat_precondition
		:parameters (?person - person ?personloc - point)
		:precondition 
			(and
				(atloc ?person ?personloc)
			)
	)
	(:action SHOP_methodm_get_to_already_there_precondition
		:parameters (?obj - object ?place - point)
		:precondition 
			(and
				(atloc ?obj ?place)
			)
	)
	(:action SHOP_methodm_get_to_person_drives_themself_precondition
		:parameters (?person - person ?place - point ?veh - vehicle ?vehloc - point)
		:precondition 
			(and
				(not (atloc ?person ?place))
				(atloc ?veh ?vehloc)
				(atloc ?person ?vehloc)
			)
	)
	(:action SHOP_methodm_get_to_vehicle_gets_driven_precondition
		:parameters (?veh - vehicle ?place - point ?vehloc - point ?person - person)
		:precondition 
			(and
				(not (atloc ?veh ?place))
				(atloc ?veh ?vehloc)
				(atloc ?person ?vehloc)
			)
	)
	(:action SHOP_methodm_get_to_as_cargo_precondition
		:parameters (?obj - object ?place - point ?objloc - point ?veh - vehicle)
		:precondition 
			(and
				(not (atloc ?obj ?place))
				(atloc ?obj ?objloc)
				(fit_in ?obj ?veh)
			)
	)
	(:action SHOP_methodm_get_to_with_ambulance_precondition
		:parameters (?obj - person ?place - point ?objloc - point ?veh - ambulance)
		:precondition 
			(and
				(not (atloc ?obj ?place))
				(atloc ?obj ?objloc)
				(fit_in ?obj ?veh)
			)
	)
	(:action SHOP_methodm_drive_to_precondition
		:parameters (?veh - vehicle ?vehloc - point ?person - adult)
		:precondition 
			(and
				(atloc ?veh ?vehloc)
				(atloc ?person ?vehloc)
				(can_drive ?person ?veh)
			)
	)
	(:action SHOP_methodm_get_in_ambulatory_person_precondition
		:parameters (?obj - person ?objloc - point ?veh - vehicle)
		:precondition 
			(and
				(atloc ?obj ?objloc)
				(atloc ?veh ?objloc)
			)
	)
	(:action SHOP_methodm_get_in_load_in_precondition
		:parameters (?obj - object ?objloc - point ?veh - vehicle ?person - person)
		:precondition 
			(and
				(atloc ?obj ?objloc)
				(atloc ?veh ?objloc)
				(can_lift ?person ?obj)
			)
	)
	(:action SHOP_methodm_get_out_unload_precondition
		:parameters (?veh - vehicle ?vehloc - point ?person - person ?obj - object)
		:precondition 
			(and
				(atloc ?veh ?vehloc)
				(can_lift ?person ?obj)
			)
	)
)
