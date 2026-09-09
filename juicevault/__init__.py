from .juicevault import JuiceVault


async def setup(bot):
    await bot.add_cog(JuiceVault(bot))
