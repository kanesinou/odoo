Basic Concepts
==============

Workflowable Type and Workflowable
----------------------------------

Management and business operations are represented by documents and contents. Every document or content type (order,
invoice, etc) likely to define procedure is a "WORKFLOWABLE TYPE". Each instance of document or
content (order XXXXX, invoice YYYYY, etc) belonging to a workflowable type is a "WORKFLOWABLE".

Stage, State and Transition
---------------------------

In practice, management documents(order, invoice, etc) pass through different levels of management. At each level, some
work is done before moving on to the next level. For example, an invoice can be initiated and filled in an office then
sent to a superior's office for review and finally sent to financial services for accounting.

The presence of the invoice at each of these levels(offices, services, etc) is represented by a "STAGE".

At each level, the completion of work on the invoice is marked by a "STATE" which can be considered as a label placed
on the document.

The movement of the invoice from one level to the other is represented by a "TRANSITION".

Therefore, the basis of procedure management consists of defining the different stages of work, the state displayed at
the completion of each step and the movements of the document between the different levels.

Route
-----

Roughly, a set of steps with their underlying transitions represents a "ROUTE". Long and complex routes can be broken
down into several sub-routes which can also be subdivided. The root route is characterized as "BASE" and the atomic
route of the subdivision is qualified as "ACTIVITY" and constitutes the wrapper of the stages. A route which is not
subdivided is therefore qualified as both a “BASE” and an “ACTIVITY”.

Procedure
---------

Defining a "PROCEDURE" is simply stipulating that a route(validation, processing, etc.) is assigned to a workflowable
type(order, invoice, etc.). In practice, this assignment may be subject to a condition.

For example, it may be defined in a procedures manual that invoices with a total exceeding a defined amount must take
another route different to the usual one. In an advanced management logic, a procedure must define a certain number of
additional parameters such as the standard duration at each step as well as access control and authorizations.

By inheriting from the taken route, a procedure can be subdivided into sub-procedures.

Process
-------

The life cycle of each document or content (order XXXXX, invoice YYYYY, etc.) whose type defines a procedure, follows
the path specified by the route defined in this procedure. This life cycle specific to each document or content
represents a “PROCESS” which progressively records events and data.

Cycle
-----

A set of "BASE" procedures can be joined to form a succession (from start to finish) of actions called "CYCLE".