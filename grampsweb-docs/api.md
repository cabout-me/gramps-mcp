
Gramps Web API

 3.2.0 

[ Base URL: /api ]

apispec.yaml

The Gramps Web API is a REST API that provides access to family tree databases generated and maintained with Gramps, a popular Open Source genealogical research software package.

    The Gramps Web API project and code are hosted at https://github.com/gramps-project/web-api

    More about Gramps and the numerous features it provides for genealogists can be found at https://gramps-project.org

GNU Affero General Public License v3.0
Schemes
people

Work with people.
GET
/people
Get information about multiple people.
POST
/people
Add a new person to the database.
GET
/people/{handle}
Get information about a specific person.
PUT
/people/{handle}
Update the person.
DELETE
/people/{handle}
Delete the person.
GET
/people/{handle}/timeline
Get the timeline for a specific person.
GET
/people/{handle}/dna/matches
Get DNA matches for a specific person.
families

Work with families.
GET
/families
Get information about multiple families.
POST
/families
Add a new family to the database.
GET
/families/{handle}
Get information about a specific family.
PUT
/families/{handle}
Update the family.
DELETE
/families/{handle}
Delete the family.
GET
/families/{handle}/timeline
Get the timeline for all the people in a specific family.
events

Work with events.
GET
/events
Get information about multiple events.
POST
/events
Add a new event to the database.
GET
/events/{handle}
Get information about a specific event.
PUT
/events/{handle}
Update the event.
DELETE
/events/{handle}
Delete the event.
GET
/events/{handle1}/span/{handle2}
Get elapsed time span between two events.
places

Work with places.
GET
/places
Get information about multiple places.
POST
/places
Add a new place to the database.
GET
/places/{handle}
Get information about a specific place.
PUT
/places/{handle}
Update the place.
DELETE
/places/{handle}
Delete the place.
citations

Work with citations.
GET
/citations
Get information about multiple citations.
POST
/citations
Add a new citation to the database.
GET
/citations/{handle}
Get information about a specific citation.
PUT
/citations/{handle}
Update the citation.
DELETE
/citations/{handle}
Delete the citation.
sources

Work with sources.
GET
/sources
Get information about multiple sources.
POST
/sources
Add a new source to the database.
GET
/sources/{handle}
Get information about a specific source.
PUT
/sources/{handle}
Update the source.
DELETE
/sources/{handle}
Delete the source.
repositories

Work with repositories.
GET
/repositories
Get information about multiple repositories.
POST
/repositories
Add a new repository to the database.
GET
/repositories/{handle}
Get information about a specific repository.
PUT
/repositories/{handle}
Update the repository.
DELETE
/repositories/{handle}
Delete the repository.
media

Work with media.
GET
/media
Get information about multiple media items.
POST
/media
Add a new media file to the database.
GET
/media/{handle}
Get information about a specific media item.
PUT
/media/{handle}
Update the media object.
DELETE
/media/{handle}
Delete the media object.
GET
/media/{handle}/file
Download a specific media item.
PUT
/media/{handle}/file
Update an existing media object's file.
GET
/media/{handle}/face_detection
Detect faces in an image.
POST
/media/{handle}/ocr
Perform text recognition (OCR) on the image.
GET
/media/{handle}/thumbnail/{size}
Download the thumbnail for a specific media item.
GET
/media/{handle}/cropped/{x1}/{y1}/{x2}/{y2}
Download the cropped version of a specific media item.
GET
/media/{handle}/cropped/{x1}/{y1}/{x2}/{y2}/thumbnail/{size}
Download the thumbnail of a cropped version of a specific media item.
POST
/media/archive/
Create an archive of media files.
GET
/media/archive/{filename}
Download the generated media archive.
POST
/media/archive/upload/zip
Upload a zipped media file archive.
notes

Work with notes.
GET
/notes
Get information about multiple notes.
POST
/notes
Add a new note to the database.
GET
/notes/{handle}
Get information about a specific note.
PUT
/notes/{handle}
Update the note.
DELETE
/notes/{handle}
Delete the note.
tags

Work with tags.
GET
/tags
Get information about multiple tags.
POST
/tags
Add a new tag to the database.
GET
/tags/{handle}
Get information about a specific tag.
PUT
/tags/{handle}
Update the tag.
DELETE
/tags/{handle}
Delete the tag.
objects

Work with primary objects.
POST
/objects
Add one or more new objects to the database.
POST
/objects/delete/
Delete all objects in the database.
transactions

Work with raw database transactions.
POST
/transactions
Commit a raw database transaction.
GET
/transactions/history/
Show the history of database transactions.
GET
/transactions/history/{transaction_id}
Show the history of database transactions.
types

Work with default and custom types.
GET
/types
Get all available default and custom Gramps record types.
GET
/types/default
Get all available Gramps default record types.
GET
/types/default/{datatype}
Get the list of values for a specific Gramps default record type.
GET
/types/default/{datatype}/map
Get the mapping for a specific Gramps default record type.
GET
/types/custom
Get all available Gramps custom record types.
GET
/types/custom/{datatype}
Get the list of values for a specific Gramps custom record type.
name-formats

Work with name formats.
GET
/name-formats
Get a list of name formats.
name-groups

Work with name group mappings.
GET
/name-groups
Get a list of name group mappings.
GET
/name-groups/{surname}
Get name group mapping for a given surname.
POST
/name-groups/{surname}/{group}
Set name group mapping for a given surname.
bookmarks

Work with bookmarks.
GET
/bookmarks
Get all bookmarks.
GET
/bookmarks/{namespace}
Get bookmarks for a given category.
PUT
/bookmarks/{namespace}/{handle}
Add a bookmark to a given category.
DELETE
/bookmarks/{namespace}/{handle}
Delte a bookmark from a given category.
filters

Work with filters.
GET
/filters
Get all custom filters and rules for all namespaces.
GET
/filters/{namespace}
Get custom filters and rules for a given namespace or category.
POST
/filters/{namespace}
Create a custom filter.
PUT
/filters/{namespace}
Update a custom filter.
GET
/filters/{namespace}/{name}
Get a custom filter for a given namespace or category.
DELETE
/filters/{namespace}/{name}
Delete a custom filter in a given namespace or category.
translations

Work with translations.
GET
/translations
Get information about available translations.
GET
/translations/{language}
Get a translation in a specific language.
POST
/translations/{language}
Get a translation in a specific language.
relations

Work with relationship calculator.
GET
/relations/{handle1}/{handle2}
Get description of most direct relationship between two people if one exists.
GET
/relations/{handle1}/{handle2}/all
Get descriptions for all possible relationships between two people if any exist.
living

Work with living calculator.
GET
/living/{handle}
Get whether or not a person is living.
GET
/living/{handle}/dates
Get estimated birth and death dates for a person.
timelines

Work with timelines.
GET
/timelines/people/
Get the timeline for a group of people.
GET
/timelines/families/
Get the timeline for all the people in a group of families.
search

Work with search engine.
GET
/search
Perform a full-text search on multiple objects.
POST
/search/index/
Trigger a reindex of the search index.
chat

Work with AI chat.
GET
/chat
Answer a chat prompt.
reports

Work with reports.
GET
/reports
Get information about available reports.
GET
/reports/{report_id}
Get information about a specific report.
GET
/reports/{report_id}/file
Get a specific report.
POST
/reports/{report_id}/file
Get a specific report.
GET
/reports/{report_id}/file/processed/{filename}
Download the generated report file.
facts

Work with record facts.
GET
/facts/
Get interesting facts about records in the tree.
holidays

Work with holiday calculator.
GET
/holidays
Get the list of countries with available holiday calendars.
GET
/holidays/{country}/{year}/{month}/{day}
Get any holiday names for the given date in the given country.
exporters

Work with exporters.
GET
/exporters
Get all exporters.
GET
/exporters/{extension}
Get a specific exporter.
GET
/exporters/{extension}/file
Get the export file generated by the given exporter.
POST
/exporters/{extension}/file
Trigger generation of the export by the given exporter.
GET
/exporters/{extension}/file/processed/{filename}
Download the export file generated by the given exporter.
metadata

Work with metadata.
GET
/metadata
Get information about the application environment and state.
authentication

Authentication services.
POST
/token
Authenticate a user to obtain a pair of JWT access tokens.
POST
/token/refresh
Obtain a fresh JWT access token.
POST
/token/create_owner/
Obtain a JWT access token that allows creating an admin or owner account if no other user exists yet.
users

Work with users.
GET
/users
Get information about registered users.
POST
/users
Create new users.
GET
/users/{user_name}
Get information about a registered user.
PUT
/users/{user_name}
Update an existing user's details.
POST
/users/{user_name}
Create a new user.
DELETE
/users/{user_name}
Delete the user.
POST
/users/{user_name}/register/
Register a new user.
POST
/users/{user_name}/create_owner/
Create an admin or owner account if no other user exists yet.
POST
/users/{user_name}/password/change
Change a user password.
POST
/users/{user_name}/password/reset/trigger
Trigger a password reset e-mail.
POST
/users/-/password/reset
Reset a user's password using a token from a reset e-mail.
GET
/users/-/password/reset
Display the password reset form.
GET
/users/-/email/confirm/
Confirm the e-mail address after user registration.
tasks
GET
/tasks/{task_id}
Return information about a task.
configuration
GET
/config
List configuration settings.
GET
/config/{key}
Return the value of a configuration setting.
PUT
/config/{key}
Update an existing setting.
POST
/config/{key}
Add a value to a setting.
DELETE
/config/{key}
Delete the setting.
importers
GET
/importers
Get all importers.
GET
/importers/{extension}
Get a specific importer.
POST
/importers/{extension}/file
Upload a file to import.
parsers
POST
/parsers/dna-match
Parse a DNA match file.
trees
GET
/trees/
Return information about multiple trees.
POST
/trees/
Create a new empty tree.
GET
/trees/{tree_id}
Return information about a tree.
PUT
/trees/{tree_id}
Update details about a tree.
POST
/trees/{tree_id}/disable
Disable a tree.
POST
/trees/{tree_id}/enable
Enable a tree.
POST
/trees/{tree_id}/migrate
Migrate a tree's Gramps database to a new schema.
POST
/trees/{tree_id}/repair
Check & repair a tree's Gramps database.
Models
JWTAccessTokens
JWTRefreshToken
JWTAccessToken
Date
Name
Surname
Attribute
Transaction
UndoTransaction
Person
PersonExtended
PersonProfile
PersonReference
Family
FamilyExtended
FamilyProfile
ChildReference
Event
EventExtended
EventProfile
EventReference
LDSOrdination
Place
PlaceExtended
PlaceName
PlaceReference
PlaceProfile
Address
Location
Citation
CitationExtended
CitationProfile
Source
SourceExtended
SourceProfile
Repository
RepositoryExtended
RepositoryReference
Media
MediaExtended
MediaReference
MediaProfile
Note
NoteExtended
StyledText
StyledTextTag
Tag
URL
FilterRuleDescription
FilterRule
CustomFilter
NamespaceFilters
Language
Translation
Relationship
Relationships
Metadata
ObjectCounts
Researcher
Bookmarks
Countries
Holidays
NameFormat
NameGroupMapping
Types
DefaultTypes
DefaultTypeMap
CustomTypes
Span
Backlinks
BacklinksExtended
PasswordChange
Credentials
Exporter
Importer
Report
ReportHelpOption
SearchResult
ChatResponse
Living
LivingDates
TimelineEventProfile
DnaMatch
DnaSegment
TimelinePersonProfile
RecordFact
RecordFactObject
TaskReference
Tree
