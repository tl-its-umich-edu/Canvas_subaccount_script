## LTI tool installation query

Use the following query in Canvas data to find LTI tool installations in Canvas instance:

```
select canvas_id, name, code, publicly_visible , workflow_state 
 from course_dim cd2 
 where id in
 (
 	select course_id
 	from course_ui_navigation_item_fact 
 	where course_ui_navigation_item_id 
 	in
 	(
		 select id
		 from course_ui_navigation_item_dim cd 
		 where id in 
		 (
			 select course_ui_navigation_item_id 
			 from course_ui_navigation_item_fact cunif 
			 where external_tool_activation_id 
			 in (
				 select id from external_tool_activation_dim etad 
				 where name = '<LTI Tool Name>' and workflow_state ='active' and activation_target_type ='account'
			 )
		 ) and visible = 'visible'
	 )
 )
order by enrollment_term_id desc
```
