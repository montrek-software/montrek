# Montrek Core Components

## Overview

This document provides an overview of the core classes used in the Montrek project, focusing on the `baseclasses` module. It aims to help new developers understand the roles and relationships of Montrek hubs and satellite models, repositories, managers, views, pages, and templates.

## Montrek Data Model

### Montrek Hub and Satellite Models

Montrek uses a Data Vault modeling approach, where data is organized into hubs and satellites.

- **MontrekHubABC**: The base class for all hub models. Hubs represent core business entities and contain only the unique identifier.
- **MontrekSatelliteABC**: The base class for all satellite models. Satellites store descriptive attributes related to a hub and are linked to the hub via a foreign key.

### Relationships

- **One-to-One Link**: Represented by `MontrekOneToOneLinkABC`.
- **One-to-Many Link**: Represented by `MontrekOneToManyLinkABC`.
- **Many-to-Many Link**: Represented by `MontrekManyToManyLinkABC`.

## Repositories

Repositories act as intermediaries between the business logic and the database. They handle data retrieval and manipulation, ensuring that the correct satellite attributes are accessed and that data follows the Data Vault logic.

- **MontrekRepository**: The base class for all repositories. It provides methods for creating, updating, and retrieving data, as well as managing annotations and linked objects.

## Managers

Managers contain business logic and interact with repositories to perform operations. They can be called by views or standalone tasks.

- **MontrekManager**: The base class for all managers. It provides methods for creating, deleting, and retrieving objects, as well as handling messages and file downloads.
- **MontrekTableManager**: A specialized manager for handling table data.
- **MontrekDetailsManager**: A specialized manager for handling detailed views of data.
- **MontrekReportManager**: A specialized manager for generating reports.

## Views

Views are responsible for collecting data and passing it to templates for rendering. They are connected to repositories for database access and can have associated managers for business logic.

- **MontrekDetailView**: Displays detailed information about a single object.
- **MontrekListView**: Displays a list of objects.
- **MontrekCreateView**: Handles the creation of new objects.
- **MontrekUpdateView**: Handles the updating of existing objects.
- **MontrekDeleteView**: Handles the deletion of objects.
- **MontrekReportView**: Generates and displays reports.

## Pages

Pages define the layout and structure of views. They can have multiple tabs, each represented by a `TabElement`, which links to different views.

- **MontrekPage**: The base class for all pages.
- **MontrekDetailsPage**: A specialized page for displaying detailed information about an object.

## Templates

Templates are HTML files that define the presentation of data. They receive context data from views and render it accordingly.
