# Gramps MCP Tools - Proper Usage Guide

## Understanding Gramps Data Structure

Gramps is fundamentally **source-focused** and **event-focused**. All genealogical information should be properly sourced and linked to verifiable events. This guide explains the correct order of operations when entering data.

## The Proper Workflow

### **FUNDAMENTAL RULE: Always Find First**
**Before creating ANY entity, always search first using the corresponding find tool.**
- If entity exists and **already contains all the new info**: Use the existing entity as-is (no update needed)
- If entity exists but **missing some of the new info**: Use `create_X` with the existing handle to **update** it
- If entity doesn't exist: Use `create_X` without handle to **create** new entity

### 1. Repository First
When you have a source document, start with the repository (archive, library, courthouse, etc.):

**Repository requires:**
- **Name** (required): "National Archives", "City Hall Records", "St. Mary's Church"
- **Type** (required): Archive, Library, Church, etc.
- **URL** (optional): If present, create with type, path, and description
- **Note** (optional): If present, use `create_note` tool first, then link to repository

**Process:**
- **First**: Use `find_repository` to search for existing repository
- **If found and complete**: Use existing repository as-is
- **If found but missing info**: Use `create_repository` with existing handle to update repository
- **If not found**: Use `create_repository` without handle to create new repository

### 2. Create the Source
Create the actual source document within the repository:

**Source requires:**
- **Title** (required): "Birth Register 1850-1860", "Marriage Book Vol. 3", "Death Certificates"
- **Repository link** (required): Handle of the repository created in step 1
- **Author** (optional): Author or compiler of the source
- **Publication info** (optional): Publisher, publication date, edition, etc.
- **Media** (optional): If present, use `create_media` tool first, then link to source
- **Note** (optional): If present, use `create_note` tool first, then link to source

**Process:**
- **First**: Use `find_source` to search for existing source document
- **If found and complete**: Use existing source as-is
- **If found but missing info**: Use `create_source` with existing handle to update source
- **If not found**: Use `create_source` without handle to create new source

### 3. Create the Citation
Create a citation that references the specific page/entry in the source:

**Citation requires:**
- **Source link** (required): Handle of the source created in step 2
- **Page** (optional): "Page 45, Entry 23", "Certificate #1234", specific page reference
- **Date** (optional): Date when the citation was accessed or created
- **Media** (optional): If present, use `create_media` tool first, then link to citation
- **Notes** (optional): If present, use `create_note` tool first, then link to citation

**Process:**
- **First**: Use `find_citation` to search for existing citation
- **If found and complete**: Use existing citation as-is
- **If found but missing info**: Use `create_citation` with existing handle to update citation
- **If not found**: Use `create_citation` without handle to create new citation

### 4. Create the Event
Now create the life event that was documented in that citation:

**Event requires:**
- **Type** (required): birth, death, marriage, baptism, burial, etc.
- **Citation** (required): Handle of the citation created in step 3
- **Date** (optional): Date when the event occurred
- **Description** (optional): Additional details about the event
- **Place** (optional): If present, use `find_place` first, then `create_place` if not found

**Process:**
- **First**: Use `find_event` to search for existing event
- **If found and complete**: Use existing event as-is
- **If found but missing info**: Use `create_event` with existing handle to update event
- **If not found**: Use `create_event` without handle to create new event

### 5. Link People to Events
**CRITICAL**: Events are linked TO people, not people to events.

#### Person Creation Attributes:
**Person requires:**
- **Given name** (required): First name(s)
- **Surname** (required): Last name(s)  
- **Gender** (required): Female, Male, or Unknown
- **Notes** (optional): If present, use `create_note` tool first, then link to person
- **Media** (optional): If present, use `create_media` tool first, then link to person
- **URLs** (optional): Web links with type, path, and description
- **Birth/Death info**: Should be added as separate birth/death events, NOT directly to person

#### For Each Person Involved:
- **First**: Use `find_person` to search for existing records
- Search by name, approximate dates, and locations
- **Always notify the user** if potential matches are found
- Ask the user to confirm if it's the same person or should be a new record

**Then for each person:**
- **If same person**: Use `create_person` with existing handle to update person AND add event with role
- **If new person**: Use `create_person` without handle to create new person (given name, surname, gender) AND add event with role

**Note**: Adding an event to a person is always an update operation using `create_person` with the person's handle.

**Person-Event linking requires:**
- **Person handle**: From find/create person process
- **Event handle**: From step 4 (the event created)
- **Role**: The person's role in the event (bride, groom, witness, child, parent, etc.)

**Important**: Birth dates, birth places, death dates, and death places should be created as separate birth/death events and linked to the person, not stored directly in the person record.

### 6. Create Family Units (when relationships exist)
**CRITICAL**: Family relationships must be supported by sourced events.

#### Family Creation Attributes:
**Family requires:**
- **Father handle** (optional): Handle of the father person
- **Mother handle** (optional): Handle of the mother person  
- **Children handles** (optional): List of handles of child persons
- **Notes** (optional): If present, use `create_note` tool first, then link to family
- **Media** (optional): If present, use `create_media` tool first, then link to family
- **URLs** (optional): Web links with type, path, and description
- **Family events**: Marriage, divorce events are added to the family unit
- **All relationships must be supported by sourced events**

#### Event Distribution:
- **Individual events** (birth, death, baptism, burial): Added to person records
- **Family events** (marriage, divorce, engagement): Added to family records

#### Process:
- **First**: Use `find_family` to search for existing family unit
- **If found and complete**: Use existing family as-is
- **If found but missing info**: Use `create_family` with existing handle to update family
- **If not found**: Use `create_family` without handle to create new family

## Example Workflow: Processing a Marriage Record

```
1. Repository: "St. Mary's Catholic Church, Boston"
   → If repository has note: create_note first, get note handle
   → find_repository (search for repository)
   → If found and complete: use existing repository
   → If found but missing info: create_repository with handle (update repository)
   → If not found: create_repository without handle (create repository with name, type, optional URL, optional note handle)

2. Source: "Marriage Register 1875-1880"  
   → If source has media: create_media first, get media handle
   → If source has note: create_note first, get note handle
   → find_source (search for document)
   → If found and complete: use existing source
   → If found but missing info: create_source with handle (update source)
   → If not found: create_source without handle (create source with title, repo link, optional author/pubinfo/abbrev/media/note handles)

3. Citation: "Page 67, Entry 15, Marriage of John Smith and Mary Jones, June 15, 1878"
   → If citation has media: create_media first, get media handle
   → If citation has notes: create_note first, get note handle
   → find_citation (search for existing citation)
   → If found and complete: use existing citation
   → If found but missing info: create_citation with handle (update citation)
   → If not found: create_citation without handle (create citation with source link, optional page/date/media/notes)

4. Event: Marriage event on June 15, 1878
   → If event has place: find_place first, create_place if not found, get place handle
   → find_event (search for existing event)
   → If found and complete: use existing event
   → If found but missing info: create_event with handle (update event)
   → If not found: create_event without handle (create event with type, citation handle, optional date/description/place handle)

5. Link People to Event:
   → If person has notes: create_note first, get note handle
   → If person has media: create_media first, get media handle
   → find_person "John Smith" (born ~1850, Boston area)
   → If matches found: Ask user to confirm identity
   → If same person: create_person with handle (update existing person) AND add event with role "groom"
   → If new person: create_person without handle (create new person with given name, surname, gender, optional notes/media/URLs) AND add event with role "groom"
   
   → If person has notes: create_note first, get note handle  
   → If person has media: create_media first, get media handle
   → find_person "Mary Jones" (born ~1855, Boston area)
   → If matches found: Ask user to confirm identity
   → If same person: create_person with handle (update existing person) AND add event with role "bride"
   → If new person: create_person without handle (create new person with given name, surname, gender, optional notes/media/URLs) AND add event with role "bride"

6. Create Family Units (when applicable):
   → If family has notes: create_note first, get note handle
   → If family has media: create_media first, get media handle
   → If creating family relationships: find_family first to check for existing family
   → If family exists and complete: use existing family
   → If family exists but missing info: create_family with handle (update family) AND add family events
   → If family doesn't exist: create_family without handle (create with father/mother/children handles, optional notes/media/URLs) AND add family events
   
   → Family events (marriage, divorce) are added to the family, not individual people
   → Individual events (birth, death) are added to people
   → All family relationships must be supported by sourced events

7. All entities now properly linked: Repository → Source → Citation → Event ← People/Families (with roles)
```

## Key Principles

### Always Source First
- Never create unsourced information
- Every fact should trace back to a citation
- Citations should reference specific pages or entries

### Check Before Creating
- **Always search before creating new people**
- Use `find_person`, `find_place`, `find_source` extensively
- Present potential matches to the user for verification
- Prevent duplicate entries through careful checking

### Maintain Data Integrity
- Link events to citations
- Link citations to sources  
- Link sources to repositories
- Connect people to events with proper roles

### User Confirmation Required
When potential duplicates are found:
- Show the user the existing record details
- Ask "Is this the same person/place, or should I create a new record?"
- Proceed based on user's decision
- Document the decision in notes if necessary

## Tool Usage Order Summary

1. `find_repository` → `create_repository` (repository: with handle to update, without handle to create)
2. `find_source` → `create_source` (source document: with handle to update, without handle to create) 
3. `find_citation` → `create_citation` (with handle to update, without handle to create)
4. `find_event` → `create_event` (with handle to update, without handle to create)
5. `find_person` → `create_person` (with handle to update, without handle to create) + link individual events
6. `find_place` → `create_place` (with handle to update, without handle to create)
7. `find_family` → `create_family` (with handle to update, without handle to create) + link family events

**Remember: ALWAYS find first, then create with handle to UPDATE or without handle to CREATE.**

**Event Distribution:**
- **Individual events** → Person records (birth, death, baptism, burial)
- **Family events** → Family records (marriage, divorce, engagement)
- **All relationships must be supported by sourced events**

## Entity Creation Details

### Creating Places
**Place requires:**
- **Name** (required): "Boston", "Massachusetts", "United States"
- **Type** (required): City, County, State, Country, Church, Cemetery, etc.
- **Enclosed by** (required): Handle of the higher-level place that contains this place
  - Example hierarchy: Church → City → County → State → Country
  - Continue until you reach Country type (top level)
- **URLs** (optional): Web links with type, path, and description

**Place Process:**
- **First**: Use `find_place` to search for existing place
- **If found and complete**: Use existing place as-is
- **If found but missing info**: Use `create_place` with existing handle to update place
- **If not found**: Use `create_place` without handle to create new place

**Place Hierarchy Example:**
```
Country: "United States" (type: Country, no enclosing place)
State: "Massachusetts" (type: State, enclosed by: United States handle)
City: "Boston" (type: City, enclosed by: Massachusetts handle)
Church: "St. Mary's Catholic Church" (type: Church, enclosed by: Boston handle)
```

### Creating Notes
**Note requires:**
- **Text** (required): The actual note content/text
- **Type** (required): General, Research, Transcript, etc.

**Note Process:**
- **First**: Use `find_note` to search for existing note (if applicable)
- **If found and complete**: Use existing note as-is
- **If found but missing info**: Use `create_note` with existing handle to update note
- **If not found**: Use `create_note` without handle to create new note

### Creating Media
**Media requires:**
- **File** (required): Path to the media file (image, document, etc.)
- **Title** (required): Descriptive title for the media
- **Date** (optional): Date when the media was created or taken

**Media Process:**
- **First**: Use `find_media` to search for existing media
- **If found and complete**: Use existing media as-is
- **If found but missing info**: Use `create_media` with existing handle to update media
- **If not found**: Use `create_media` without handle to create new media

## Date Format Specification

**IMPORTANT**: All dates in Gramps use a specific structure with multiple components:

**Date Components:**
- **Year** (required): Four-digit year (e.g., 1878)
- **Month** (optional): Month number (1-12)
- **Day** (optional): Day of month (1-31)
- **Type** (required): Date precision/range type
  - `regular`: Exact date
  - `before`: Before this date
  - `after`: After this date
  - `about`: Approximate date (circa)
  - `range`: Between two dates
  - `span`: Duration/period
  - `from`: From this date onward
  - `to`: Up to this date
- **Quality** (required): Date reliability
  - `regular`: Normal/certain date
  - `estimated`: Estimated date (circa)
  - `calculated`: Calculated from other information

**Date Examples:**
- Exact date: Year=1878, Month=6, Day=15, Type=regular, Quality=regular
- Estimated: Year=1850, Type=regular, Quality=estimated
- Before date: Year=1860, Type=before, Quality=regular
- Date range: Start(Year=1875), End(Year=1880), Type=range, Quality=regular

This date structure applies to ALL date fields throughout the system: events, media, citations, etc.

This workflow ensures proper genealogical methodology and maintains the integrity of the family tree data.