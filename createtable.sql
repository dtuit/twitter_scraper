DROP TABLE IF EXISTS [dbo].[Twitter_Statuses]
DROP TABLE IF EXISTS [dbo].[Twitter_Users]
DROP TABLE IF EXISTS [dbo].[Twitter_Statuses_Staging]
DROP TABLE IF EXISTS [dbo].[Twitter_Users_Staging]
DROP TABLE IF EXISTS [dbo].[Twitter_Staging]


CREATE TABLE [dbo].[Twitter_Staging](
	[Id] int IDENTITY PRIMARY KEY NONCLUSTERED,
	[InfoJson] nvarchar(max) NOT NULL,
	[DateInjested] datetime2 NOT NULL,
	[DateProcessed] datetime2 Null,
)

--CREATE TABLE [dbo].[Twitter_Users_Staging]
--(
--	[Id] int IDENTITY(1,1) NOT NULL PRIMARY KEY,
--	[UserId] NUMERIC(20) NOT NULL,
--	[CreatedAt] DATETIME2 NULL,
--	[UserName] nvarchar(20) NOT NULL,
--	[ScreenName] nvarchar(20) NULL,
--	[ProfileImageUrl] varchar(200) NULL,
--	[Verified] Bit NULL,
--)

--CREATE TABLE [dbo].[Twitter_Statuses_Staging](
--	[Id] int IDENTITY(1,1) NOT NULL PRIMARY KEY,
--	[TweetId] [numeric](20, 0) NOT NULL,
--	[UserId] [numeric](20, 0) NOT NULL,
--	[CreatedAt] [datetime2](7) NOT NULL,
--	[Text] [nvarchar](max) NOT NULL,
--	[Sentiment] [nvarchar](max) NULL,
--	[RetweetCount] [int] NULL,
--	[FavoriteCount] [int] NULL,
--	[HashTags] [nvarchar](max) NULL,
--	[Symbols] [nvarchar](max) NULL,
--	[UserMentions] [nvarchar](max) NULL,
--	[Urls] [nvarchar](max) NULL,
--	[DummyVideo] [bit] NULL,
--	[DummyImage] [bit] NULL,
--	[QuotedStatusId] [numeric](20, 0) NULL,
--	[InReplyToUserId] [numeric](20,0) NULL,
--	[DateInserted] [datetime2] NOT NULL, 
--	[DateUpdated] [datetime2] NULL,
--)

CREATE TABLE [dbo].[Twitter_Users]
(
	[UserId] NUMERIC(20) NOT NULL PRIMARY KEY,
	[CreatedAt] DATETIME2 NULL,
	[UserName] nvarchar(20) NOT NULL,
	[ScreenName] nvarchar(20) NULL,
	[ProfileImageUrl] varchar(200) NULL,
	[Verified] Bit NULL,
	[DateInjested] [datetime2] NOT NULL, 
	[DateUpdated] [datetime2] NULL
)

--CREATE TABLE [dbo].[Twitter_Tags](
--	[Id] IDENTITY(1,1) NOT NULL,
--	[Tag] varchar(240) NOT NULL,
--	[TagType] varchar
--)

CREATE TABLE [dbo].[Twitter_Statuses](
	[Id] NUMERIC(20) IDENTITY(1,1) NOT NULL,
	[TweetId] [numeric](20, 0) NOT NULL PRIMARY KEY,
	[UserId] [numeric](20, 0) NOT NULL CONSTRAINT FK_Statuses_Users FOREIGN KEY REFERENCES Twitter_Users(UserId),
	[CreatedAt] [datetime2](7) NOT NULL,
	[Text] [nvarchar](max) NOT NULL,
	[Sentiment] [nvarchar](max) NULL,
	[RetweetCount] [int] NULL,
	[FavoriteCount] [int] NULL,
	[HashTags] [nvarchar](max) NULL,
	[Symbols] [nvarchar](max) NULL,
	[UserMentions] [nvarchar](max) NULL,
	[Urls] [nvarchar](max) NULL,
	[DummyVideo] [bit] NULL,
	[DummyImage] [bit] NULL,
	[QuotedStatusId] [numeric](20, 0) NULL CONSTRAINT FK_Statuses_QuotedStatus FOREIGN KEY REFERENCES Twitter_Statuses(TweetId),
	[InReplyToUserId] [numeric](20,0) NULL,
	[DateInjested] [datetime2] NOT NULL, 
	[DateUpdated] [datetime2] NULL
)

