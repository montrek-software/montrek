# Montrek Apps

In Montrek, every logical enitiy should be self contained in a app. These entities should be small enough to make maintanence as easiy as possible and clear enough such that there is no surprise, where something is happening. These apps are based on the typical django adds, but expect a few more components, which will be explained in the following section.

## models

This is a models file that follows the django models idea. Every ORM instance is defined in here. But instead of inheriting from django models, the models defined in here should be based on the Montrek Base Models. If a app stores data, in here at least a Hub and a Satellite should be defined. A closer look at the Montrek Data Model can be found in **here** (TODO Add link once sections written).

## Repositories

No business logic part of the code should access the models directly, but call methods of the repository class. The repository is the linker between whatever parts wants to access or write data and the models. Every repository class has a `std_queryset` method, in which the typical queryset for calling a data object, with the corresponding satellite attributes and links is defined in here. In case at some points other queries are necessary, they can also be defined in here. The base methods of `MontrekRepository` make sure, that the correct satellite atrributes at a given state date are given and that writing new objects follow the Data Vault logic. 

The querysets from other repositories can be called from here in case access to the data from other models is needed.

## Views

At the core of every request is a view. The purpose of this class is to collect all the data that is necessary to pass on to the template, such that the desired outcome is displayed correctly. It is connected to a repository object, which handles the communication to the database. Multiple views have a page attributed it, if the purpose of the view is to input data, it can have a form attached. If the view is supposed to trigger business logic, it can have a manager class attached to it.

Montrek comes with a number of pre-defined which are optimised for the Montrek Data Model:

### MontrekDetailView

This accesses the `std_queryset` of the repository and displays the object with the pk passed via the url. Its `elements` proprty needs to be filled with `TableElements`, which define the name and the type of data that is shown.

## Pages

The pages object deals with the layout of the page. Many views can share the same page class. The most prominent feature of the page class is the tabs row. Each page can have a number of `TabElements`, which store the url to the target view that the user is directed to, when clicking on it. 
